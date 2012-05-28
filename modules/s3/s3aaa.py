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
           "S3RoleMatrix",
           "FaceBookAccount",
           "GooglePlusAccount",
          ]

import datetime
import re
import time
import uuid
import urllib
from urllib import urlencode
import urllib2

from gluon import *
from gluon.storage import Storage, Messages

from gluon.dal import Field, Row, Query, Set, Table, Expression
from gluon.sqlhtml import CheckboxesWidget, StringWidget
from gluon.tools import Auth, callback, addrow
from gluon.utils import web2py_uuid
from gluon.validators import IS_SLUG
from gluon.contrib import simplejson as json
from gluon.contrib.simplejson.ordered_dict import OrderedDict
from gluon.contrib.login_methods.oauth20_account import OAuthAccount

from s3method import S3Method
from s3validators import IS_ACL
from s3widgets import S3ACLWidget, CheckboxesWidgetS3

from s3utils import s3_mark_required
from s3fields import s3_uid, s3_timestamp, s3_deletion_status

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

            - s3_register
            - s3_link_to_organisation
            - s3_link_to_person
            - s3_approver
            - s3_verify_email_onaccept
            - s3_register_staff

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
        self.messages.registration_pending_approval = "Account registered, however registration is still pending approval - please wait until confirmation received."
        self.messages.email_approver_failed = "Failed to send mail to Approver - see if you can notify them manually!"
        self.messages.email_verification_failed = "Unable to send verification email - either your email is invalid or our email server is down"
        self.messages.email_sent = "Verification Email sent - please check your email to validate. If you do not receive this email please check you junk email or spam filters"
        self.messages.email_verified = "Email verified - you can now login"
        self.messages.welcome_email_subject = "Welcome to %(system_name)s" % \
            dict(system_name=system_name)
        self.messages.welcome_email = \
            "Welcome to %(system_name)s - click on the link %(url)s to complete your profile" % \
                dict(system_name = system_name,
                     url = deployment_settings.get_base_public_url() + URL("default", "user", args=["profile"]))
        self.messages.duplicate_email = "This email address is already in use"
        self.messages.registration_disabled = "Registration Disabled!"
        self.messages.registration_verifying = "You haven't yet Verified your account - please check your email"
        self.messages.label_organisation_id = "Organization"
        self.messages.label_site_id = "Facility"
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
                                      cr_shelter = shelter,
                                      #org_facility = T("Facility"),
                                      org_facility = T("Site"),
                                      org_office = T("Office"),
                                      hms_hospital = T("Hospital"),
                                      #project_site = T("Project Site"),
                                      #fire_station = T("Fire Station"),
                                      dvi_morgue = T("Morgue"),
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
        request = current.request
        session = current.session
        settings = self.settings
        messages = self.messages

        # User table
        if not settings.table_user:
            passfield = settings.password_field
            if settings.username_field:
                # with username (not used by default in Sahana)
                settings.table_user = db.define_table(
                    settings.table_user_name,
                    Field("first_name", length=128, default="",
                          label=messages.label_first_name),
                    Field("last_name", length=128, default="",
                          label=messages.label_last_name),
                    Field("username", length=128, default="",
                          unique=True),
                    Field(passfield, "password", length=512,
                          readable=False, label=messages.label_password),
                    Field("email", length=512, default="",
                          label=messages.label_email),
                    Field("language", length=16),
                    Field("utc_offset", length=16,
                          readable=False, writable=False),
                    Field("organisation_id", "integer",
                          writable=False,
                          label=messages.label_organisation_id),
                    Field("site_id", "integer",
                          writable=False,
                          label=messages.label_site_id),
                    Field("registration_key", length=512,
                          writable=False, readable=False, default="",
                          label=messages.label_registration_key),
                    Field("reset_password_key", length=512,
                          writable=False, readable=False, default="",
                          label=messages.label_registration_key),
                    Field("deleted", "boolean", writable=False,
                          readable=False, default=False),
                    Field("timestmp", "datetime", writable=False,
                          readable=False, default=""),
                    migrate = migrate,
                    fake_migrate=fake_migrate,
                    *(s3_uid()+s3_timestamp()))
            else:
                # with email-address (Sahana default)
                settings.table_user = db.define_table(
                    settings.table_user_name,
                    Field("first_name", length=128, default="",
                          label=messages.label_first_name),
                    Field("last_name", length=128, default="",
                          label=messages.label_last_name),
                    Field("email", length=512, default="",
                          label=messages.label_email,
                          unique=True),
                    Field(passfield, "password", length=512,
                          readable=False, label=messages.label_password),
                    Field("language", length=16),
                    Field("utc_offset", length=16,
                          readable=False,
                          writable=False,
                          label=messages.label_utc_offset),
                    Field("organisation_id", "integer",
                          writable=False,
                          label=messages.label_organisation_id),
                    Field("site_id", "integer",
                          writable=False,
                          label=messages.label_site_id),
                    Field("registration_key", length=512,
                          writable=False, readable=False, default="",
                          label=messages.label_registration_key),
                    Field("reset_password_key", length=512,
                          writable=False, readable=False, default="",
                          label=messages.label_registration_key),
                    Field("deleted", "boolean", writable=False,
                          readable=False, default=False),
                    Field("timestmp", "datetime", writable=False,
                          readable=False, default=""),
                    migrate = migrate,
                    fake_migrate=fake_migrate,
                    *(s3_uid()+s3_timestamp()))

            table = settings.table_user
            table.first_name.notnull = True
            table.first_name.requires = \
                IS_NOT_EMPTY(error_message=messages.is_empty)
            if current.deployment_settings.get_L10n_mandatory_lastname():
                table.last_name.notnull = True
                table.last_name.requires = \
                    IS_NOT_EMPTY(error_message=messages.is_empty)
            table.utc_offset.comment = A(SPAN("[Help]"),
                                         _class="tooltip",
                                         _title="%s|%s" % (messages.label_utc_offset,
                                                           messages.help_utc_offset))
            try:
                from s3validators import IS_UTC_OFFSET
                table.utc_offset.requires = IS_EMPTY_OR(IS_UTC_OFFSET())
            except:
                pass
            table[passfield].requires = [CRYPT(key=settings.hmac_key,
                                               min_length=self.settings.password_min_length,
                                               digest_alg="sha512")]
            if settings.username_field:
                table.username.requires = IS_NOT_IN_DB(db,
                                                       "%s.username" % settings.table_user._tablename)
            table.email.requires = \
                [IS_EMAIL(error_message=messages.invalid_email),
                 IS_LOWER(),
                 IS_NOT_IN_DB(db,
                              "%s.email" % settings.table_user._tablename,
                              error_message=messages.duplicate_email)]
            table.registration_key.default = ""

        # Group table (roles)
        if not settings.table_group:
            settings.table_group = db.define_table(
                settings.table_group_name,
                # Group unique ID, must be notnull+unique:
                Field("uuid",
                      length=64,
                      notnull=True,
                      unique=True,
                      readable=False,
                      writable=False),
                # Group does not appear in the Role Manager:
                # (can neither assign, nor modify, nor delete)
                Field("hidden", "boolean",
                      readable=False,
                      writable=False,
                      default=False),
                # Group cannot be modified in the Role Manager:
                # (can assign, but neither modify nor delete)
                Field("system", "boolean",
                      readable=False,
                      writable=False,
                      default=False),
                # Group cannot be deleted in the Role Manager:
                # (can assign and modify, but not delete)
                Field("protected", "boolean",
                      readable=False,
                      writable=False,
                      default=False),
                # Role name:
                Field("role",
                      length=512,
                      default="",
                      unique=True,
                      label=messages.label_role),
                Field("description", "text",
                      label=messages.label_description),
                migrate = migrate,
                fake_migrate=fake_migrate,
                *(s3_timestamp()+s3_deletion_status()))
            table = settings.table_group
            table.role.requires = IS_NOT_IN_DB(db, "%s.role"
                 % settings.table_group._tablename)

        # Group membership table (user<->role)
        if not settings.table_membership:
            settings.table_membership = db.define_table(
                settings.table_membership_name,
                Field("user_id", settings.table_user,
                      label=messages.label_user_id),
                Field("group_id", settings.table_group,
                      label=messages.label_group_id),
                Field("pe_id", "integer"),
                migrate = migrate,
                fake_migrate=fake_migrate,
                *(s3_uid()+s3_timestamp()+s3_deletion_status()))

            table = settings.table_membership
            table.user_id.requires = IS_IN_DB(db, "%s.id" %
                    settings.table_user._tablename,
                    "%(id)s: %(first_name)s %(last_name)s")
            table.group_id.requires = IS_IN_DB(db, "%s.id" %
                    settings.table_group._tablename,
                    "%(id)s: %(role)s")

        security_policy = current.deployment_settings.get_security_policy()
        # Define Eden permission table
        self.permission.define_table(migrate=migrate,
                                     fake_migrate=fake_migrate)

        if security_policy not in (1, 2, 3, 4, 5, 6, 7, 8) and \
           not settings.table_permission:
            # Permissions table (group<->permission)
            # NB This Web2Py table is deprecated / replaced in Eden by S3Permission
            settings.table_permission = db.define_table(
                settings.table_permission_name,
                Field("group_id", settings.table_group,
                      label=messages.label_group_id),
                Field("name", default="default", length=512,
                      label=messages.label_name),
                Field("table_name", length=512,
                      label=messages.label_table_name),
                Field("record_id", "integer",
                      label=messages.label_record_id),
                migrate = migrate,
                fake_migrate=fake_migrate)
            table = settings.table_permission
            table.group_id.requires = IS_IN_DB(db, "%s.id" %
                    settings.table_group._tablename,
                    "%(id)s: %(role)s")
            table.name.requires = IS_NOT_EMPTY()
            table.table_name.requires = IS_IN_SET(db.tables)
            table.record_id.requires = IS_INT_IN_RANGE(0, 10 ** 9)

        # Event table (auth log)
        # Records Logins & ?
        # @ToDo: Deprecate? At least make it configurable?
        if not settings.table_event:
            settings.table_event = db.define_table(
                settings.table_event_name,
                Field("time_stamp", "datetime",
                      default=request.now,
                      label=messages.label_time_stamp),
                Field("client_ip",
                      default=request.client,
                      label=messages.label_client_ip),
                Field("user_id", settings.table_user, default=None,
                      requires = IS_IN_DB(db, "%s.id" %
                                          settings.table_user._tablename,
                                          "%(id)s: %(first_name)s %(last_name)s"),
                      label=messages.label_user_id),
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

        request = current.request
        session = current.session
        db = current.db

        table_user = self.settings.table_user
        table_membership = self.settings.table_membership

        if self.settings.login_userfield:
            userfield = self.settings.login_userfield
        elif "username" in table_user.fields:
            userfield = "username"
        else:
            userfield = "email"
        passfield = self.settings.password_field
        user = db(table_user[userfield] == username).select().first()
        password = table_user[passfield].validate(password)[0]
        if user:
            user_id = user.id
            if not user.registration_key and user[passfield] == password:
                user = Storage(table_user._filter_fields(user, id=True))
                session.auth = Storage(user=user,
                                       last_visit=request.now,
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

        response = current.response

        response.cookies["registered"] = "yes"
        response.cookies["registered"]["expires"] = 365 * 24 * 3600 # 1 year
        response.cookies["registered"]["path"] = "/"

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
        table_user = self.settings.table_user
        if self.settings.login_userfield:
            username = self.settings.login_userfield
        elif "username" in table_user.fields:
            username = "username"
        else:
            username = "email"
        old_requires = table_user[username].requires
        table_user[username].requires = [IS_NOT_EMPTY(), IS_LOWER()]
        request = current.request
        response = current.response
        session = current.session
        passfield = self.settings.password_field
        try:
            table_user[passfield].requires[-1].min_length = 0
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
                table_user,
                fields=[username, passfield],
                hidden=dict(_next=request.vars._next),
                showid=self.settings.showid,
                submit_button=self.messages.submit_button,
                delete_label=self.messages.delete_label,
                formstyle=self.settings.formstyle,
                separator=self.settings.label_separator
                )
            if self.settings.remember_me_form:
                # Add a new input checkbox "remember me for longer"
                addrow(form,XML("&nbsp;"),
                       DIV(XML("&nbsp;"),
                           INPUT(_type='checkbox',
                                 _class='checkbox',
                                 _id="auth_user_remember",
                                 _name="remember",
                                 ),
                           XML("&nbsp;&nbsp;"),
                           LABEL(
                            self.messages.label_remember_me,
                            _for="auth_user_remember",
                            )),"",
                       self.settings.formstyle,
                       'auth_user_remember__row')

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
                query = (table_user[username] == form.vars[username])
                user = db(query).select().first()
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
                user = self.get_or_create_user(table_user._filter_fields(cas_user))
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
            user = Storage(table_user._filter_fields(user, id=True))
            # If the user hasn't set a personal UTC offset,
            # then read the UTC offset from the form:
            if not user.utc_offset:
                user.utc_offset = session.s3.utc_offset
            session.auth = Storage(
                user=user,
                last_visit=request.now,
                expiration = request.vars.get("remember", False) and \
                    self.settings.long_expiration or self.settings.expiration,
                remember = request.vars.has_key("remember"),
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
            db(table_user.id == self.user.id).update(timestmp = request.utcnow)
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
            table_user[username].requires = old_requires
            return form
        else:
            redirect(next)

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
        response = current.response
        session = current.session
        deployment_settings = current.deployment_settings

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

        user = settings.table_user

        passfield = settings.password_field

        # S3: Organisation field in form?
        if deployment_settings.get_auth_registration_requests_organisation():
            # Widget set in controllers/default.py
            #user.organisation_id.widget =
            user.organisation_id.writable = True
            if deployment_settings.get_auth_registration_organisation_mandatory():
                user.organisation_id.comment = SPAN("*", _class="req")
            else:
                user.organisation_id.comment = DIV(_class="tooltip",
                                                   _title="%s|%s" % (messages.label_organisation_id,
                                                                     messages.help_organisation))
        else:
            user.organisation_id.readable = False
            user.organisation_id.writable = False
        user.organisation_id.default = deployment_settings.get_auth_registration_organisation_id_default()
        # @ToDo: Option to request Facility during Registration
        user.site_id.readable = False
        labels, required = s3_mark_required(user)
        #formstyle = current.manager.s3.crud.formstyle
        form = SQLFORM(user, hidden=dict(_next=request.vars._next),
                       labels = labels,
                       separator = "",
                       showid=settings.showid,
                       submit_button=messages.submit_button,
                       delete_label=messages.delete_label,
                       #formstyle = formstyle
                       )
        for i, row in enumerate(form[0].components):
            item = row[1][0]
            if isinstance(item, INPUT) and item["_name"] == passfield:
                field_id = "%s_password_two" % user._tablename
                #row = formstyle(...)
                form[0].insert(i + 1, TR(
                        TD(LABEL("%s:" % messages.verify_password,
                                 _for="password_two",
                                 _id=field_id + SQLFORM.ID_LABEL_SUFFIX),
                           _class="w2p_fl"),
                        INPUT(_name="password_two",
                              _id=field_id,
                              _type="password",
                              requires=IS_EXPR("value==%s" % \
                              repr(request.vars.get(passfield, None)),
                              error_message=messages.mismatched_password)),
                        SPAN("*", _class="req"),
                "", _id=field_id + SQLFORM.ID_ROW_SUFFIX))
                #form[0].insert(i + 1, row)
        # add an opt in clause to receive emails depending on the deployment settings
        if deployment_settings.get_auth_opt_in_to_email():
            field_id = "%s_opt_in" % user._tablename
            comment = DIV(DIV(_class="tooltip",
                            _title="%s|%s" % ("Mailing list",
                                              "By selecting this you agree that we may contact you.")))
            checked = deployment_settings.get_auth_opt_in_default() and "selected"
            form[0].insert(-1,
                           TR(TD(LABEL("%s:" % "Receive updates",
                                       _for="opt_in",
                                       _id=field_id + SQLFORM.ID_LABEL_SUFFIX),
                                 _class="w2p_fl"),
                                 INPUT(_name="opt_in", _id=field_id, _type="checkbox", _checked=checked),
                              TD(comment,
                                 _class="w2p_fc"),
                           _id=field_id + SQLFORM.ID_ROW_SUFFIX))

        # S3: Insert Mobile phone field into form
        if deployment_settings.get_auth_registration_requests_mobile_phone():
            field_id = "%s_mobile" % user._tablename
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
            field_id = "%s_image" % user._tablename
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

        import uuid
        user.registration_key.default = key = str(uuid.uuid4())

        if form.accepts(request.vars, session, formname="register",
                        onvalidation=onvalidation):

            if settings.create_user_groups:
                # Not used in S3
                description = \
                    "group uniquely assigned to %(first_name)s %(last_name)s"\
                     % form.vars
                group_id = self.add_group("user_%s" % form.vars.id,
                                          description)
                self.add_membership(group_id, form.vars.id)

            approved = False
            users = db(settings.table_user.id > 0).count()
            if users == 1:
                # 1st user to register shouldn't need verification/approval
                approved = True

            elif settings.registration_requires_verification:
                # Ensure that we add to the correct Organization
                approver, organisation_id = self.s3_approver(form.vars)

                if organisation_id:
                    # @ToDo: Is it correct to override the organisation entered by the user?
                    #        Ideally (if the deployment_settings.auth.registration_requests_organisation = True
                    #        the org could be selected based on the email and the user could then override
                    form.vars.organisation = organisation_id

                # Send the Verification email
                if not settings.mailer or \
                   not settings.mailer.send(to=form.vars.email,
                                            subject=messages.verify_email_subject,
                                            message=messages.verify_email % dict(key=key)):
                    db.rollback()
                    response.error = messages.email_verification_failed
                    return form
                # @ToDo: Deployment Setting?
                #session.confirmation = messages.email_sent
                next = URL(c="default", f="message",
                           args = ["verify_email_sent"],
                           vars = {"email": form.vars.email})

            elif settings.registration_requires_approval:
                # Identify the Approver &
                # ensure that we add to the correct Organization
                approver, organisation_id = self.s3_approver(form.vars)
                if organisation_id:
                    form.vars.organisation_id = organisation_id

                if approver:
                    # Send the Authorisation email
                    form.vars.approver = approver
                    if not settings.mailer or \
                        not settings.verify_email_onaccept(form.vars):
                        # We don't wish to prevent registration if the approver mail fails to send
                        #db.rollback()
                        session.error = messages.email_approver_failed
                        #return form
                    user[form.vars.id] = dict(registration_key="pending")
                    session.warning = messages.registration_pending_approval
                else:
                    # The domain is Whitelisted
                    approved = True
            else:
                # No verification or approval needed
                approved = True
                approver, organisation_id = self.s3_approver(form.vars)
                if organisation_id:
                    form.vars.organisation = organisation_id
                form.vars.registration_key = ""
                form.vars.approver = approver
                settings.verify_email_onaccept(form.vars)

            # Set a Cookie to present user with login box by default
            self.set_cookie()

            if approved:
                user[form.vars.id] = dict(registration_key="")
                session.confirmation = messages.registration_successful

                table_user = settings.table_user
                if "username" in table_user.fields:
                    username = "username"
                else:
                    username = "email"
                query = (table_user[username] == form.vars[username])
                user = db(query).select(limitby=(0, 1)).first()
                user = Storage(table_user._filter_fields(user, id=True))

                if users == 1:
                    # Add the first user to admin group
                    admin_group_id = 1
                    self.add_membership(admin_group_id, user.id)

                # If the user hasn't set a personal UTC offset,
                # then read the UTC offset from the form:
                if not user.utc_offset:
                    user.utc_offset = session.s3.utc_offset
                session.auth = Storage(user=user, last_visit=request.now,
                                       expiration=settings.expiration)
                self.user = user
                session.flash = messages.logged_in

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
    def verify_email(self,
                     next=DEFAULT,
                     onaccept=DEFAULT,
                     log=DEFAULT):
        """
            action user to verify the registration email, XXXXXXXXXXXXXXXX

            .. method:: Auth.verify_email([next=DEFAULT [, onvalidation=DEFAULT
                [, onaccept=DEFAULT [, log=DEFAULT]]]])
        """

        db = current.db

        settings = self.settings
        messages = self.messages
        deployment_settings = current.deployment_settings

        key = current.request.args[-1]
        table_user = settings.table_user
        user = db(table_user.registration_key == key).select().first()
        if not user:
            redirect(settings.verify_email_next)
        # S3: Lookup the Approver
        approver, organisation_id = self.s3_approver(user)
        if settings.registration_requires_approval and approver:
            user.update_record(registration_key = "pending")
            current.session.flash = messages.registration_pending_approval
        else:
            user.update_record(registration_key = "")
            current.session.flash = messages.email_verified
        if log == DEFAULT:
            log = messages.verify_email_log
        if next == DEFAULT:
            next = settings.verify_email_next
        if onaccept == DEFAULT:
            onaccept = settings.verify_email_onaccept
        if log:
            self.log_event(log % user)

        if approver:
            user.approver = approver
            callback(onaccept, user)

        redirect(next)

    # -------------------------------------------------------------------------
    def profile(
        self,
        next=DEFAULT,
        onvalidation=DEFAULT,
        onaccept=DEFAULT,
        log=DEFAULT,
        ):
        """
            returns a form that lets the user change his/her profile

            .. method:: Auth.profile([next=DEFAULT [, onvalidation=DEFAULT
                [, onaccept=DEFAULT [, log=DEFAULT]]]])

            Patched for S3 to use s3_mark_required
        """

        table_user = self.settings.table_user
        if not self.is_logged_in():
            redirect(self.settings.login_url)
        passfield = self.settings.password_field
        self.settings.table_user[passfield].writable = False
        request = current.request
        session = current.session
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
        labels, required = s3_mark_required(table_user)
        form = SQLFORM(
            table_user,
            self.user.id,
            fields = self.settings.profile_fields,
            labels = labels,
            hidden = dict(_next=next),
            showid = self.settings.showid,
            submit_button = self.messages.profile_save_button,
            delete_label = self.messages.delete_label,
            upload = self.settings.download_url,
            formstyle = self.settings.formstyle,
            separator=""
            )
        if form.accepts(request, session,
                        formname='profile',
                        onvalidation=onvalidation,hideerror=self.settings.hideerror):
            self.user.update(table_user._filter_fields(form.vars))
            session.flash = self.messages.profile_updated
            if log:
                self.log_event(log % self.user)
            callback(onaccept,form)
            if not next:
                next = self.url(args=request.args)
            elif isinstance(next, (list, tuple)): ### fix issue with 2.6
                next = next[0]
            elif next and not next[0] == '/' and next[:4] != 'http':
                next = self.url(next.replace('[id]', str(form.vars.id)))
            redirect(next)
        return form

    # -------------------------------------------------------------------------
    # S3 User Registration Post-Processing
    # -------------------------------------------------------------------------
    def s3_register(self, form):
        """
            S3 framework function

            Designed to be used as an onaccept callback for register()

            Whenever someone registers, it:
                - adds them to the 'Authenticated' role
                - adds their name to the Person Registry
                - creates their profile picture
                - creates an HRM record
                - adds them to the Org_x Access role

            @param form: the registration form
        """

        db = current.db
        manager = current.manager
        s3db = current.s3db

        vars = form.vars
        user_id = vars.id
        if not user_id:
            return None

        # Add to 'Authenticated' role
        authenticated = self.id_group("Authenticated")
        self.add_membership(authenticated, user_id)

        # Link to organisation, lookup the pe_id of the organisation
        organisation_id = self.s3_link_to_organisation(vars)
        if organisation_id:
            otable = s3db.org_organisation
            query = (otable.id == organisation_id)
            org = db(query).select(otable.pe_id).first()
            if org:
                owned_by_entity = org.pe_id
        else:
            owned_by_entity = None

        # Add to Person Registry and Email/Mobile to pr_contact
        person_id = self.s3_link_to_person(vars, # user
                                           owned_by_entity)

        # Insert the profile picture
        if "image" in vars:
            if hasattr(vars.image, "file"):
                source_file = vars.image.file
                original_filename = vars.image.filename
                ptable = s3db.pr_person
                query = (ptable.id == person_id)
                pe_id = db(query).select(ptable.pe_id,
                                         limitby=(0, 1)).first()
                if pe_id:
                    pe_id = pe_id.pe_id
                    itable = s3db.pr_image
                    field = itable.image
                    newfilename = field.store(source_file,
                                              original_filename,
                                              field.uploadfolder)
                    url = URL(c="default", f="download", args=newfilename)
                    fields = dict(pe_id=pe_id,
                                  profile=True,
                                  image=newfilename,
                                  url = url,
                                  title=current.T("Profile Picture"))
                    if isinstance(field.uploadfield, str):
                        fields[field.uploadfield] = source_file.read()
                    itable.insert(**fields)

        # Create an HRM entry, if one doesn't already exist
        htablename = "hrm_human_resource"
        htable = s3db.table(htablename)
        if htable and organisation_id:

            query = (htable.person_id == person_id) & \
                    (htable.organisation_id == organisation_id)
            row = db(query).select(htable.id, limitby=(0, 1)).first()

            if not row:
                if current.deployment_settings.get_hrm_show_staff():
                    type = 1 # Staff
                else:
                    type = 2 # Volunteer
                record = Storage(person_id=person_id,
                                 organisation_id=organisation_id,
                                 type=type,
                                 owned_by_user=user_id,
                                 owned_by_entity=owned_by_entity)
                record_id = htable.insert(**record)
                if record_id:
                    record["id"] = record_id
                    manager.model.update_super(htable, record)
                    manager.onaccept(htablename, record, method="create")

        # Return person_id for init scripts
        return person_id

    # -------------------------------------------------------------------------
    def s3_link_to_organisation(self, user):
        """
            Link a user account to an organisation

            @param user: the user account record (= form.vars in s3_register)
        """

        db = current.db
        s3db = current.s3db
        manager = current.manager
        model = manager.model

        organisation_id = user.organisation_id
        if not organisation_id:
            otable = s3db.org_organisation
            name = user.get("organisation_name", None)
            acronym = user.get("organisation_acronym", None)
            if name:
                # Create new organisation
                record = Storage(name=name,
                                 acronym=acronym)
                organisation_id = otable.insert(**record)

                # Callbacks
                if organisation_id:
                    record["id"] = organisation_id
                    model.update_super(otable, record)
                    manager.onaccept(otable, record, method="create")
                    self.s3_set_record_owner(otable, organisation_id)

                # Update user
                user.organisation_id = organisation_id
                query = (utable.id == user_id)
                db(query).update(organisation_id=organisation_id)

        if not organisation_id:
            return None

        # Create link (if it doesn't exist)
        user_id = user.id
        ltable = s3db.org_organisation_user
        if ltable:
            query = (ltable.user_id == user_id) & \
                    (ltable.organisation_id == organisation_id)
            row = db(query).select(ltable.id, limitby=(0, 1)).first()
            if not row:
                ltable.insert(user_id=user_id,
                              organisation_id=organisation_id)

        return organisation_id

    # -------------------------------------------------------------------------
    def s3_link_to_person(self,
                          user=None,
                          owned_by_entity=None):
        """
            Links user accounts to person registry entries

            @param user: the user record
            @param owned_by_entity: the pe_id of the owner organisation

            Policy for linking to pre-existing person records:

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
        ptable = s3db.pr_person
        ctable = s3db.pr_contact
        atable = s3db.pr_address
        etable = s3db.pr_pentity
        ttable = s3db.sit_trackable
        gtable = s3db.gis_config

        ltable = s3db.pr_person_user

        left = [ltable.on(ltable.user_id == utable.id),
                ptable.on(ptable.pe_id == ltable.pe_id)]
        if user is not None:
            if not isinstance(user, (list, tuple)):
                user = [user]
            user_ids = [u.id for u in user]
            query = (utable.id.belongs(user_ids))
        else:
            query = (utable.id != None)
        users = db(query).select(utable.id,
                                 utable.first_name,
                                 utable.last_name,
                                 utable.email,
                                 ltable.pe_id,
                                 ptable.id,
                                 left=left, distinct=True)

        utn = utable._tablename

        person_ids = [] # Collect the person IDs
        for u in users:

            person = u.pr_person
            if person.id is not None:
                person_ids.append(person.id)
                continue

            user = u[utn]

            owner = Storage(owned_by_user=user.id,
                            owned_by_entity=owned_by_entity)

            if "email" in user:

                # Try to find a matching person record
                first_name = user.first_name
                last_name = user.last_name
                email = user.email.lower()
                query = (ptable.first_name == first_name) & \
                        (ptable.last_name == last_name) & \
                        (ctable.pe_id == ptable.pe_id) & \
                        (ctable.contact_method == "EMAIL") & \
                        (ctable.value.lower() == email)
                person = db(query).select(ptable.id,
                                          ptable.pe_id,
                                          limitby=(0, 1)).first()

                if person and \
                   not db(ltable.pe_id == person.pe_id).count():
                    # Match found, and it isn't linked to another user account

                    # Insert a link
                    ltable.insert(user_id=user.id, pe_id=person.pe_id)

                    # Assign ownership of the Person record
                    person.update_record(**owner)

                    # Assign ownership of the Contact record(s)
                    query = (ctable.pe_id == person.pe_id)
                    db(query).update(**owner)

                    # Assign ownership of the Address record(s)
                    query = (atable.pe_id == person.pe_id)
                    db(query).update(**owner)

                    # Assign ownership of the Config record(s)
                    query = (gtable.pe_id == person.pe_id)
                    db(query).update(**owner)

                    # HR records
                    self.s3_register_staff(user.id, person.id)

                    # Set pe_id if this is the current user
                    if self.user and self.user.id == user.id:
                        self.user.pe_id = person.pe_id

                    person_ids.append(person.id)
                    continue

                # Create a PE
                pe_id = etable.insert(instance_type="pr_person",
                                      deleted=False)
                # Create a TE
                track_id = ttable.insert(instance_type="pr_person",
                                         deleted=False)
                if pe_id:

                    # Create a new person record
                    if current.request.vars.get("opt_in", None):
                        opt_in = current.deployment_settings.get_auth_opt_in_team_list()
                    else:
                        opt_in = ""
                    new_id = ptable.insert(pe_id = pe_id,
                                           track_id = track_id,
                                           first_name = first_name,
                                           last_name = last_name,
                                           opt_in = opt_in,
                                           modified_by = user.id,
                                           **owner)

                    if new_id:

                        # Insert a link
                        ltable.insert(user_id=user.id, pe_id=pe_id)

                        # Register the new person UUID in the PE and TE
                        person_uuid = ptable[new_id].uuid
                        db(etable.id == pe_id).update(uuid=person_uuid)
                        db(ttable.id == track_id).update(uuid=person_uuid)

                        # Add the email to pr_contact
                        ctable.insert(pe_id = pe_id,
                                      contact_method = "EMAIL",
                                      priority = 1,
                                      value = email,
                                      **owner)

                        # Add the mobile to pr_contact
                        mobile = current.request.vars.get("mobile", None)
                        if mobile:
                            ctable.insert(
                                    pe_id = pe_id,
                                    contact_method = "SMS",
                                    priority = 2,
                                    value = mobile,
                                    **owner)
                        person_ids.append(new_id)

                        # Add the user to each team if they have chosen to opt-in
                        g_table = s3db["pr_group"]
                        gm_table = s3db["pr_group_membership"]
                        for team in opt_in:
                            query = (g_table.name == team)
                            team_rec = db(query).select(g_table.id, limitby=(0, 1)).first()
                            # if the team doesn't exist then add it
                            if team_rec == None:
                                team_id = g_table.insert(name = team, group_type = 5)
                            else:
                                team_id = team_rec.id
                            gm_table.insert(group_id = team_id,
                                            person_id = new_id)

                    # Set pe_id if this is the current user
                    if self.user and self.user.id == user.id:
                        self.user.pe_id = pe_id

        if len(person_ids) == 1:
            return person_ids[0]
        else:
            return person_ids

    # -------------------------------------------------------------------------
    def s3_approver(self, user):
        """
            Returns the Approver for a new Registration &
            the organisation_id field

            @param: user - the user record (form.vars when done direct)
        """

        db = current.db
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        # Default Approver
        approver = deployment_settings.get_mail_approver()
        organisation_id = None
        # Check for Domain: Whitelist or specific Approver
        table = s3db.auth_organisation
        address, domain = user.email.split("@", 1)
        query = (table.domain == domain)
        record = db(query).select(table.organisation_id,
                                  table.approver,
                                  limitby=(0, 1)).first()
        if record:
            organisation_id = record.organisation_id
            approver = record.approver

        elif deployment_settings.get_auth_registration_requests_organisation():
            # Check for an Organization-specific Approver
            organisation_id = user.get("organisation_id",
                                       None)
            if organisation_id:
                query = (table.organisation_id == organisation_id)
                record = db(query).select(table.approver,
                                          limitby=(0, 1)).first()
                if record and record.approver:
                    approver = record.approver

        return approver, organisation_id

    # -------------------------------------------------------------------------
    def s3_verify_email_onaccept(self, form):
        """"
            Sends a message to the approver to notify them if a user needs approval
            If deployment_settings.auth.always_notify_approver = True,
            send them notification regardless
        """

        if form.registration_key == "": # User Approved
            if not current.deployment_settings.get_auth_always_notify_approver():
                return
            subject = current.T("%(system_name)s - New User Registered") % \
                      {"system_name": current.deployment_settings.get_system_name()}
            message = self.messages.new_user % dict(first_name = form.first_name,
                                                        last_name = form.last_name,
                                                        email = form.email)
        else:
            subject = current.T("%(system_name)s - New User Registration Approval Pending") % \
                      {"system_name": current.deployment_settings.get_system_name()}
            message = self.messages.approve_user % \
                        dict(first_name=form.first_name,
                             last_name=form.last_name,
                             email=form.email)

        result = self.settings.mailer.send(to=form.approver,
                                           subject=subject,
                                           message=message)

        return result

    # -------------------------------------------------------------------------
    def s3_register_staff(self, user_id, person_id):
        """
            Take ownership of the HR records of the person record,
            and add user to the Org Access role.

            To be called by s3_link_to_person in case a newly registered
            user record gets linked to a prior existing person record.

            @param user_id: the user record ID
            @param person_id: the person record ID
        """

        db = current.db
        s3db = current.s3db
        manager = current.manager

        htable = s3db.table("hrm_human_resource")
        if htable is None:
            # HR module disabled: skip
            return
        rtable = self.settings.table_group
        mtable = self.settings.table_membership
        utable = self.settings.table_user

        # User owns their own HRM records
        query = (htable.person_id == person_id)
        db(query).update(owned_by_user=user_id)

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

        self.settings.mailer.send(user["email"], subject=subject, message=message)

    # -------------------------------------------------------------------------
    # S3-specific authentication methods
    # -------------------------------------------------------------------------
    def s3_impersonate(self, user_id):
        """
            S3 framework function

            Designed to be used within tasks, which are run in a separate request
            & hence don't have access to current.auth

            @param user_id: auth.user.id or auth.user.email
        """

        session = current.session
        db = current.db

        table_user = self.settings.table_user
        query = None
        if not user_id:
            # Anonymous
            self.user = None
        elif isinstance(user_id, basestring) and not user_id.isdigit():
            if self.settings.username_field:
                query = (table_user.username == user_id)
            else:
                query = (table_user.email == user_id)
        else:
            query = (table_user.id == user_id)

        if query is not None:
            user = db(query).select(limitby=(0, 1)).first()
            if not user:
                # Invalid user ID
                raise ValueError("User not found")
            else:
                self.user = Storage(table_user._filter_fields(user, id=True))

        self.s3_set_roles()

        if self.user:
            # Set the language from the Profile
            language = user.language
            current.T.force(language)
            current.session.s3.language = language

        return self.user

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
            into the current session. To be run once per session, as these
            IDs should never change.
        """

        session = current.session

        try:
            if session.s3.system_roles:
                return session.s3.system_roles
        except:
            pass

        db = current.db
        gtable = self.settings.table_group
        if gtable is not None:
            system_roles = self.S3_SYSTEM_ROLES
            query = (gtable.deleted != True) & \
                     gtable.uuid.belongs(system_roles.values())
            rows = db(query).select(gtable.id, gtable.uuid)
            sr = Storage([(role.uuid, role.id) for role in rows])
        else:
            sr = Storage([(uid, None) for uid in self.S3_SYSTEM_ROLES])

        session.s3.system_roles = sr
        return sr

    # -------------------------------------------------------------------------
    def s3_set_roles(self):
        """ Update pe_id, roles and realms for the current user """

        session = current.session

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
            import uuid
            uid = uuid.uuid4()

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
        s3db = current.s3db

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
        s3db = current.s3db

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
        mtable = self.settings.table_membership

        if not user_id:
            return []

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

        db = current.db
        session = current.session

        # Trigger HTTP basic auth
        self.s3_logged_in()

        # Get the realms
        if not session.s3:
            return False
        if self.user:
            realms = self.user.realms
        else:
            realms = Storage([(r, None) for r in session.s3.roles])
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
                row = db(query).select(gtable.id, limitby=(0, 1)).first()
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

        db = current.db
        s3db = current.s3db

        if not self.permission.delegations:
            return False
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

        db = current.db
        s3db = current.s3db

        if not self.permission.delegations:
            return False
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

        db = current.db
        s3db = current.s3db

        if not entity or not self.permission.delegations:
            return None
        dtable = s3db.table("pr_delegation")
        rtable = s3db.table("pr_role")
        atable = s3db.table("pr_affiliation")
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
        rows = db(query).select(atable.pe_id,
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
    def s3_get_user_id(self, person_id):
        """
            Get the user_id for a person_id

            @param person_id: the pr_person record ID
        """
        db = current.db
        s3db = current.s3db

        if isinstance(person_id, basestring) and not person_id.isdigit():
            utable = self.settings.table_user
            query = (utable.email == person_id)
            user = db(query).select(utable.id,
                                    limitby=(0, 1)).first()
            if user:
                return user.id
        else:
            ptable = s3db.table("pr_person")
            ltable = s3db.table("pr_person_user")
            if ptable and ltable:
                query = (ptable.id == person_id) & \
                        (ptable.pe_id == ltable.pe_id)
                link = db(query).select(ltable.user_id,
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

        db = current.db
        s3db = current.s3db

        ltable = s3db.pr_person_user
        query = (ltable.user_id == user_id)
        row = db(query).select(ltable.pe_id, limitby=(0, 1)).first()
        if row:
            return row.pe_id
        return None

    # -------------------------------------------------------------------------
    def s3_logged_in_person(self):
        """
            Get the person record ID for the current logged-in user
        """

        db = current.db
        s3db = current.s3db
        ptable = s3db.pr_person

        if self.s3_logged_in():
            try:
                query = (ptable.pe_id == self.user.pe_id)
            except AttributeError:
                # Prepop
                pass
            else:
                record = db(query).select(ptable.id,
                                          limitby=(0, 1)).first()
                if record:
                    return record.id
        return None

    # -------------------------------------------------------------------------
    def s3_logged_in_human_resource(self):
        """
            Get the first HR record ID for the current logged-in user
        """

        db = current.db
        s3db = current.s3db
        ptable = s3db.pr_person
        htable = s3db.hrm_human_resource

        if self.s3_logged_in():
            try:
                query = (htable.person_id == ptable.id) & \
                        (ptable.pe_id == self.user.pe_id)
            except AttributeError:
                # Prepop
                pass
            else:
                record = db(query).select(htable.id,
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

        db = current.db

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
                    record = db(query).select(table.owned_by_user,
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

        db = current.db
        session = current.session
        T = current.T

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
        session.warning = T("Only showing accessible records!")
        membership = self.settings.table_membership
        permission = self.settings.table_permission
        return table.id.belongs(db(membership.user_id == user_id)\
                                  (membership.group_id == permission.group_id)\
                                  (permission.name == method)\
                                  (permission.table_name == table)\
                                  ._select(permission.record_id))


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
                    request = current.request
                    next = URL(args=request.args, vars=request.get_vars)
                    import urllib
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
                records = current.session.owned_records.get(table, [])
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
    def s3_update_record_owner(self, table, record, **fields):
        """
            Update the ownership for a record

            @param table: the table
            @param record: the record or record ID
            @param fields: dict of {ownership_field:value}
        """

        db = current.db
        ownership_fields = ("owned_by_user",
                            "owned_by_group",
                            "owned_by_entity")
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
            return db(table._id == record_id).update(**data)
        else:
            return None

    # -------------------------------------------------------------------------
    def s3_set_record_owner(self, table, record, **fields):
        """
            Update the record owner, to be called from CRUD and Importer

            @param table: the table (or table name)
            @param record: the record (or record ID)
            @keyword owned_by_user: the auth_user ID of the owner user
            @keyword owned_by_group: the auth_group ID of the owner group
            @keyword owned_by_entity: the pe_id of the owner entity, or a tuple
                                      (instance_type, instance_id) to lookup the
                                      pe_id from
        """

        db = current.db
        s3db = current.s3db
        model = current.manager.model

        # Ownership fields
        OUSR = "owned_by_user"
        OGRP = "owned_by_group"
        OENT = "owned_by_entity"
        ownership_fields = (OUSR, OGRP, OENT)

        # Entity reference fields
        EID = "pe_id"
        OID = "organisation_id"
        SID = "site_id"
        GID = "group_id"
        PID = "person_id"
        entity_fields = (EID, OID, SID, GID, PID)

        # Entity tables
        otablename = "org_organisation"
        stablename = "org_site"
        gtablename = "pr_group"
        ptablename = "pr_person"

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
        fields_in_table += [f for f in entity_fields if f in table]

        # Get all available fields for the record
        fields_missing = [f for f in fields_in_table if f not in record]
        if fields_missing:
            fields_to_load = [table._id]+[table[f] for f in fields_in_table]
            query = table._id == record_id
            row = db(query).select(limitby=(0, 1), *fields_to_load).first()
        else:
            row = record
        if not row:
            return

        # Prepare the udpate
        data = Storage()

        # Find owned_by_user
        if OUSR in fields_in_table:
            if OUSR in fields:
                data[OUSR] = fields[OUSR]
            elif row[OUSR]:
                pass
            else:
                user_id = None
                # Records which link to a person_id shall be owned by that person
                if tablename == "pr_person":
                    user_id = self.s3_get_user_id(row[table._id])
                elif PID in row:
                    user_id = self.s3_get_user_id(row[PID])
                if not user_id and self.s3_logged_in() and self.user:
                    # Fallback to current user
                    user_id = self.user.id
                if user_id:
                    data[OUSR] = user_id

        # Find owned_by_group
        if OGRP in fields_in_table:
            # Check for type-specific handler to find the owner group
            handler = model.get_config(tablename, "owner_group")
            if handler:
                if callable(handler):
                    data[OGRP] = handler(table, row)
                else:
                    data[OGRP] = handler
            # Otherwise, only set if explicitly specified
            elif OGRP in fields:
                data[OGRP] = fields[OGRP]

        # Find owned_by_entity
        if OENT in fields_in_table:
            if OENT in fields:
                data[OENT] = fields[OENT]
            elif not row[OENT]:
                # Check for type-specific handler to find the owner entity
                handler = model.get_config(tablename, "owner_entity")
                if callable(handler):
                    owner_entity = handler(table, row)
                    data[OENT] = owner_entity
                # Otherwise, do a fallback cascade
                else:
                    get_pe_id = s3db.pr_get_pe_id
                    if EID in row and tablename not in ("pr_person", "dvi_body"):
                        owner_entity = row[EID]
                    elif OID in row:
                        owner_entity = get_pe_id(otablename, row[OID])
                    elif SID in row:
                        owner_entity = get_pe_id(stablename, row[SID])
                    elif GID in row:
                        owner_entity = get_pe_id(gtablename, row[GID])
                    else:
                        owner_entity = None
                    if owner_entity:
                        data["owned_by_entity"] = owner_entity

        self.s3_update_record_owner(table, row, **data)
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

        db = current.db
        s3db = current.s3db
        T = current.T
        ERROR = T("You do not have permission for any facility to perform this action.")
        HINT = T("Create a new facility or ensure that you have permissions for an existing facility.")

        if not error_msg:
            error_msg = ERROR

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
                rows = db(query).select(ftable.site_id)
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
            current.manager.configure(tablename, insertable = False)

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

        db = current.db
        s3db = current.s3db
        manager = current.manager
        T = current.T
        ERROR = T("You do not have permission for any organization to perform this action.")
        HINT = T("Create a new organization or ensure that you have permissions for an existing organization.")

        if not error_msg:
            error_msg = ERROR

        org_table = s3db.org_organisation
        query = self.s3_accessible_query("update", org_table)
        query &= (org_table.deleted == False)
        rows = db(query).select(org_table.id)
        if rows:
            return [org.id for org in rows]
        request = current.request
        if "update" in request.args or "create" in request.args:
            if redirect_on_error:
                manager.session.error = error_msg + " " + HINT
                redirect(URL(c="default", f="index"))
        elif table is not None:
            if hasattr(table, "_tablename"):
                tablename = table._tablename
            else:
                tablename = table
            manager.configure(tablename, insertable = False)

        return []

# =============================================================================
class S3Permission(object):
    """ S3 Class to handle permissions """

    TABLENAME = "s3_permission"

    CREATE = 0x0001
    READ = 0x0002
    UPDATE = 0x0004
    DELETE = 0x0008

    ALL = CREATE | READ | UPDATE | DELETE
    NONE = 0x0000 # must be 0!

    PERMISSION_OPTS = OrderedDict([
        #(NONE, "NONE"),
        #(READ, "READ"),
        #(CREATE|UPDATE|DELETE, "WRITE"),
        [CREATE, "CREATE"],
        [READ, "READ"],
        [UPDATE, "UPDATE"],
        [DELETE, "DELETE"]])

    # Method string <-> required permission
    METHODS = Storage({
        "create": CREATE,
        "import": CREATE,
        "read": READ,
        "report": READ,
        "search": READ,
        "update": UPDATE,
        "delete": DELETE})

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

        # Instantiated once per request, but before Auth tables
        # are defined and authentication is checked, thus no use
        # to check permissions in the constructor

        # Store auth reference in self because current.auth is not
        # available at this point yet, but needed in define_table.
        self.auth = auth

        settings = current.deployment_settings

        # Policy: which level of granularity do we want?
        self.policy = settings.get_security_policy()
        # ACLs to control access per controller:
        self.use_cacls = self.policy in (3, 4, 5, 6, 7 ,8)
        # ACLs to control access per function within controllers:
        self.use_facls = self.policy in (4, 5, 6, 7, 8)
        # ACLs to control access per table:
        self.use_tacls = self.policy in (5, 6, 7, 8)
        # Authorization takes owner entity into account:
        self.entity_realm = self.policy in (6, 7, 8)
        # Permissions shared along the hierarchy of entities:
        self.entity_hierarchy = self.policy in (7, 8)
        # Permission sets can be delegated:
        self.delegations = self.policy == 8

        # Permissions table
        self.tablename = tablename or self.TABLENAME
        self.table = current.db.get(self.tablename, None)

        # Error messages
        T = current.T
        self.INSUFFICIENT_PRIVILEGES = T("Insufficient Privileges")
        self.AUTHENTICATION_REQUIRED = T("Authentication Required")

        # Request information
        request = current.request
        self.controller = request.controller
        self.function = request.function

        # Request format
        # @todo: move this into s3tools.py:
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
                            # of the owner entity
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
                   fields (id, owned_by_user, owned_by_group, owned_by_entity),
                   otherwise the record will be re-loaded by this function.

            @returns: tuple of (owner_entity, owner_group, owner_user)
        """

        owner_entity = None
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
        ownership_fields = ("owned_by_entity",
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

        if "owned_by_entity" in record:
            owner_entity = record["owned_by_entity"]
        if "owned_by_group" in record:
            owner_group = record["owned_by_group"]
        if "owned_by_user" in record:
            owner_user = record["owned_by_user"]
        return (owner_entity, owner_group, owner_user)

    # -------------------------------------------------------------------------
    def is_owner(self, table, record, owners=None):
        """
            Check whether the current user owns the record

            @param table: the table or tablename
            @param record: the record ID (or the Row if already loaded)
            @param owners: override the actual record owners by a tuple
                           (owner_entity, owner_group, owner_user)

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
            owner_entity, owner_group, owner_user = \
                    owners
        elif record:
            owner_entity, owner_group, owner_user = \
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
        if not owner_entity and \
           not owner_group and \
           not owner_user:
            return True

        # OrgAuth:
        # apply only group memberships with are valid for the owner entity
        if self.entity_realm and owner_entity:
            realms = self.auth.user.realms
            roles = [sr.ANONYMOUS]
            append = roles.append
            for r in realms:
                realm = realms[r]
                if realm is None or owner_entity in realm:
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
        OENT = "owned_by_entity"

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
        OENT = "owned_by_entity"

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

        if not isinstance(method, (list, tuple)):
            method = [method]
        if record == 0:
            record = None
        _debug("\nhas_permission('%s', c=%s, f=%s, t=%s, record=%s)" % \
               (",".join(method), c, f, t, record))

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
        _debug("==> racl: %04X" % racl)

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
            raise RuntimeError("Cannot determine permission.")
        elif permitted:
            _debug("*** GRANTED ***")
        else:
            _debug("*** DENIED ***")

        response.s3.permissions[key] = permitted

        return permitted

    # -------------------------------------------------------------------------
    def accessible_query(self, method, table, c=None, f=None):
        """
            Returns a query to select the accessible records for method
            in table.

            @param method: the method as string or a list of methods (AND)
            @param table: the database table or table name
            @param c: controller name (falls back to current request)
            @param f: function name (falls back to current request)
        """

        if not hasattr(table, "_tablename"):
            tablename = table
            table = current.s3db.table(tablename)
            if not table:
                raise AttributeError("undefined table %s" % tablename)

        if not isinstance(method, (list, tuple)):
            method = [method]
        _debug("\naccessible_query(%s, '%s')" % (table, ",".join(method)))

        # Defaults
        ALL_RECORDS = (table._id > 0)
        NO_RECORDS = (table._id == 0)

        # Auth override, system roles and login
        auth = self.auth
        if self.auth.override:
            _debug("==> auth.override")
            _debug("*** ALL RECORDS ***")
            return ALL_RECORDS
        sr = auth.get_system_roles()
        logged_in = auth.s3_logged_in()

        # Required ACL
        racl = self.required_acl(method)
        _debug("==> racl: %04X" % racl)

        # Get realms and delegations
        user = auth.user
        if not logged_in:
            realms = Storage({sr.ANONYMOUS:None})
            delegations = Storage()
        else:
            realms = user.realms
            delegations = user.delegations

        # Administrators have all permissions
        if sr.ADMIN in realms:
            _debug("==> user is ADMIN")
            _debug("*** ALL RECORDS ***")
            return ALL_RECORDS

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
            _debug("*** NO RECORDS ***")
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

        OENT = "owned_by_entity"

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
            @param entity: the owner entity

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

        sr = self.auth.get_system_roles()
        modules = current.deployment_settings.modules

        hidden_modules = []
        if self.use_cacls:
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
           "owned_by_entity" not in table.fields:
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
        if "ANY" in acls or acls and "owned_by_entity" not in table.fields:
            return False

        # In all other cases: yes
        return True

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
        self.table = db.get(tablename, None)
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

        settings = current.session.s3

        #print >>sys.stderr, "Audit %s: %s_%s record=%s representation=%s" % \
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
            if settings.audit_read:
                table.insert(timestmp = now,
                             person = self.user,
                             operation = operation,
                             tablename = tablename,
                             record = record,
                             representation = representation)

        elif operation in ("create", "update"):
            if settings.audit_write:
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
            if settings.audit_write:
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

        output = dict()

        request = self.request
        response = current.response
        resource = self.resource
        manager = current.manager
        auth = manager.auth

        db = current.db
        table = self.table

        T = current.T

        if r.id:
            return self._edit(r, **attr)

        # Show permission matrix?
        show_matrix = request.get_vars.get("matrix", False) and True

        if r.interactive:

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
                    acls[any][c][any] = Storage(oacl = auth.permission.NONE,
                                                uacl = auth.permission.NONE)

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
                                       args=[role_id], vars=request.get_vars),
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
                                          vars=request.get_vars),
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
                        options = auth.permission.PERMISSION_OPTS
                        NONE = auth.permission.NONE
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
            response.s3.actions = []
            response.s3.no_sspag = True

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
        model = manager.model
        acl_table = auth.permission.table

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
            acl_table.oacl.requires = IS_ACL(auth.permission.PERMISSION_OPTS)
            acl_table.uacl.requires = IS_ACL(auth.permission.PERMISSION_OPTS)
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
            key_row = P(T("* Required Fields"), _class="red")
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
                        if auth.permission.use_facls:
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
                                  uacl = auth.permission.NONE,
                                  oacl = auth.permission.NONE)
                if c in acls:
                    acl_list = acls[c]
                    if any not in acl_list:
                        acl_list[any] = default
                else:
                    acl_list = Storage(ANY=default)
                acl = acl_list[any]
                _class = i % 2 and "even" or "odd"
                i += 1
                uacl = auth.permission.NONE
                oacl = auth.permission.NONE
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
            if auth.permission.use_facls:
                _class = auth.permission.use_tacls and \
                         "tab_other" or "tab_last"
                tabs.append(SPAN(A(FACL, _class="facl-tab"), _class=_class))
            if auth.permission.use_tacls:
                tabs.append(SPAN(A(TACL, _class="tacl-tab"),
                                 _class="tab_last"))

            acl_forms.append(DIV(DIV(tabs, _class="tabs"),
                                     TABLE(thead, TBODY(form_rows)),
                                     _id="controller-acls"))

            # Function ACL table ----------------------------------------------
            if auth.permission.use_facls:

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
                        uacl = auth.permission.NONE
                        oacl = auth.permission.NONE
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
                    TD(acl_widget("uacl", "new_c_uacl", auth.permission.NONE)),
                    TD(acl_widget("oacl", "new_c_oacl", auth.permission.NONE)),
                    TD(new_acl), _class=_class))

                # Tabs to change to the other view
                tabs = [SPAN(A(CACL, _class="cacl-tab"),
                             _class="tab_other"),
                        SPAN(A(FACL), _class="tab_here")]
                if auth.permission.use_tacls:
                    tabs.append(SPAN(A(TACL, _class="tacl-tab"),
                                     _class="tab_last"))

                acl_forms.append(DIV(DIV(tabs, _class="tabs"),
                                         TABLE(thead, TBODY(form_rows)),
                                         _id="function-acls"))

            # Table ACL table -------------------------------------------------

            if auth.permission.use_tacls:
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
                    uacl = auth.permission.NONE
                    oacl = auth.permission.NONE
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
                    TD(acl_widget("uacl", "new_t_uacl", auth.permission.NONE)),
                    TD(acl_widget("oacl", "new_t_oacl", auth.permission.NONE)),
                    TD(new_acl), _class=_class))

                # Tabs
                tabs = [SPAN(A(CACL, _class="cacl-tab"),
                             _class="tab_other")]
                if auth.permission.use_facls:
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
                    import uuid
                    role.uuid = uuid.uuid4()
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
                edit_btn = A(T("Edit User Account %s" % user_name),
                             _href=URL(c="admin", f="user",
                                       args=[user_id]),
                             _class="action-lnk")
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
                              edit_btn=edit_btn,
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

        types = ("org_organisation", "org_office", "pr_group")
        entities = s3db.pr_get_entities(types=types, group=True)

        for instance_type in entities:
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
class FaceBookAccount(OAuthAccount):
    """ OAuth implementation for FaceBook """

    AUTH_URL = "https://graph.facebook.com/oauth/authorize"
    TOKEN_URL = "https://graph.facebook.com/oauth/access_token"

    # -------------------------------------------------------------------------
    def __init__(self):

        from facebook import GraphAPI, GraphAPIError

        self.GraphAPI = GraphAPI
        self.GraphAPIError = GraphAPIError
        g = dict(GraphAPI=GraphAPI,
                 GraphAPIError=GraphAPIError,
                 request=current.request,
                 response=current.response,
                 session=current.session,
                 HTTP=HTTP)
        client = current.auth.settings.facebook
        OAuthAccount.__init__(self, g, client["id"], client["secret"],
                              self.AUTH_URL, self.TOKEN_URL,
                              scope="email,user_about_me,user_location,user_photos,user_relationships,user_birthday,user_website,create_event,user_events,publish_stream")
        self.graph = None

    # -------------------------------------------------------------------------
    def login_url(self, next="/"):
        """ Overriding to produce a different redirect_uri """

        request = current.request
        session = current.session
        if not self.accessToken():
            if not request.vars.code:
                session.redirect_uri = "%s/%s/default/facebook/login" % \
                    (current.deployment_settings.get_base_public_url(),
                     request.application)
                data = dict(redirect_uri=session.redirect_uri,
                            response_type="code",
                            client_id=self.client_id)
                if self.args:
                    data.update(self.args)
                auth_request_url = self.auth_url + "?" + urlencode(data)
                raise HTTP(307,
                           "You are not authenticated: you are being redirected to the <a href='" + auth_request_url + "'> authentication server</a>",
                           Location=auth_request_url)
            else:
                session.code = request.vars.code
                self.accessToken()
                #return session.code
        return next

    # -------------------------------------------------------------------------
    def get_user(self):
        """ Returns the user using the Graph API. """

        db = current.db
        auth = current.auth
        session = current.session

        if not self.accessToken():
            return None

        if not self.graph:
            self.graph = self.GraphAPI((self.accessToken()))

        user = None
        try:
            user = self.graph.get_object_c("me")
        except self.GraphAPIError:
            self.session.token = None
            self.graph = None

        if user:
            # Check if a user with this email has already registered
            #session.facebooklogin = True
            table = auth.settings.table_user
            query = (table.email == user["email"])
            existent = db(query).select(table.id,
                                        table.password,
                                        limitby=(0, 1)).first()
            if existent:
                #session["%s_setpassword" % existent.id] = existent.password
                _user = dict(first_name = user.get("first_name", ""),
                             last_name = user.get("last_name", ""),
                             facebookid = user["id"],
                             facebook = user.get("username", user["id"]),
                             email = user["email"],
                             password = existent.password
                            )
                return _user
            else:
                # b = user["birthday"]
                # birthday = "%s-%s-%s" % (b[-4:], b[0:2], b[-7:-5])
                # if 'location' in user:
                #     session.flocation = user['location']
                #session["is_new_from"] = "facebook"
                auth.s3_send_welcome_email(user)
                # auth.initial_user_permission(user)  # Called on profile page
                _user = dict(first_name = user.get("first_name", ""),
                             last_name = user.get("last_name", ""),
                             facebookid = user["id"],
                             facebook = user.get("username", user["id"]),
                             nickname = IS_SLUG()(user.get("username", "%(first_name)s-%(last_name)s" % user) + "-" + user['id'][:5])[0],
                             email = user["email"],
                             # birthdate = birthday,
                             about = user.get("bio", ""),
                             website = user.get("website", ""),
                             # gender = user.get("gender", "Not specified").title(),
                             photo_source = 3,
                             tagline = user.get("link", ""),
                             registration_type = 2,
                            )
                return _user

# =============================================================================
class GooglePlusAccount(OAuthAccount):
    """
        OAuth implementation for Google
        https://code.google.com/apis/console/
    """

    AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
    TOKEN_URL = "https://accounts.google.com/o/oauth2/token"
    API_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

    # -------------------------------------------------------------------------
    def __init__(self):

        request = current.request
        settings = current.deployment_settings

        g = dict(request=request,
                 response=current.response,
                 session=current.session,
                 HTTP=HTTP)

        client = current.auth.settings.google

        self.globals = g
        self.client = client
        self.client_id = client["id"]
        self.client_secret = client["secret"]
        self.auth_url = self.AUTH_URL
        self.args = dict(
                scope = "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile",
                user_agent = "google-api-client-python-plus-cmdline/1.0",
                xoauth_displayname = settings.get_system_name(),
                response_type = "code",
                redirect_uri = "%s/%s/default/google/login" % \
                    (settings.get_base_public_url(),
                     request.application),
                approval_prompt = "force",
                state = "google"
            )
        self.graph = None

    # -------------------------------------------------------------------------
    def __build_url_opener(self, uri):
        """
            Build the url opener for managing HTTP Basic Athentication
        """
        # Create an OpenerDirector with support
        # for Basic HTTP Authentication...

        auth_handler = urllib2.HTTPBasicAuthHandler()
        auth_handler.add_password(None,
                                  uri,
                                  self.client_id,
                                  self.client_secret)
        opener = urllib2.build_opener(auth_handler)
        return opener

    # -------------------------------------------------------------------------
    def accessToken(self):
        """
            Return the access token generated by the authenticating server.

            If token is already in the session that one will be used.
            Otherwise the token is fetched from the auth server.
        """

        session = current.session

        if session.token and session.token.has_key("expires"):
            expires = session.token["expires"]
            # reuse token until expiration
            if expires == 0 or expires > time.time():
                return session.token["access_token"]
        if session.code:
            data = dict(client_id = self.client_id,
                        client_secret = self.client_secret,
                        redirect_uri = self.args["redirect_uri"],
                        code = session.code,
                        grant_type = "authorization_code",
                        scope = "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile")

            # if self.args:
            #     data.update(self.args)
            open_url = None
            opener = self.__build_url_opener(self.TOKEN_URL)
            try:
                open_url = opener.open(self.TOKEN_URL, urlencode(data))
            except urllib2.HTTPError, e:
                raise Exception(e.read())
            finally:
                del session.code # throw it away

            if open_url:
                try:
                    session.token = json.loads(open_url.read())
                    session.token["expires"] = int(session.token["expires_in"]) + \
                        time.time()
                finally:
                    opener.close()
                return session.token["access_token"]

        session.token = None
        return None

    # -------------------------------------------------------------------------
    def login_url(self, next="/"):
        """ Overriding to produce a different redirect_uri """

        request = current.request
        session = current.session
        if not self.accessToken():
            if not request.vars.code:
                session.redirect_uri = self.args["redirect_uri"]
                data = dict(redirect_uri=session.redirect_uri,
                            response_type="code",
                            client_id=self.client_id)
                if self.args:
                    data.update(self.args)
                auth_request_url = self.auth_url + "?" + urlencode(data)
                raise HTTP(307,
                           "You are not authenticated: you are being redirected to the <a href='" + auth_request_url + "'> authentication server</a>",
                           Location=auth_request_url)
            else:
                session.code = request.vars.code
                self.accessToken()
                #return session.code
        return next

    # -------------------------------------------------------------------------
    def get_user(self):
        """ Returns the user using the Graph API. """

        db = current.db
        auth = current.auth
        session = current.session

        if not self.accessToken():
            return None

        user = None
        try:
            user = self.call_api()
        except Exception, e:
            session.token = None

        if user:
            # Check if a user with this email has already registered
            #session.googlelogin = True
            table = auth.settings.table_user
            query = (table.email == user["email"])
            existent = db(query).select(table.id,
                                        table.password,
                                        limitby=(0, 1)).first()
            if existent:
                #session["%s_setpassword" % existent.id] = existent.password
                _user = dict(
                            #first_name = user.get("given_name", user["name"]),
                            #last_name = user.get("family_name", user["name"]),
                            googleid = user["id"],
                            email = user["email"],
                            password = existent.password
                            )
                return _user
            else:
                # b = user["birthday"]
                # birthday = "%s-%s-%s" % (b[-4:], b[0:2], b[-7:-5])
                # if "location" in user:
                #     session.flocation = user["location"]
                #session["is_new_from"] = "google"
                auth.s3_send_welcome_email(user)
                _user = dict(
                            first_name = user.get("given_name", user["name"].split()[0]),
                            last_name = user.get("family_name", user["name"].split()[-1]),
                            googleid = user["id"],
                            nickname = "%(first_name)s-%(last_name)s-%(id)s" % dict(first_name=user["name"].split()[0].lower(), last_name=user["name"].split()[-1].lower(), id=user['id'][:5]),
                            email = user["email"],
                            # birthdate = birthday,
                            website = user.get("link", ""),
                            # gender = user.get("gender", "Not specified").title(),
                            photo_source = 6 if user.get("picture", None) else 2,
                            googlepicture = user.get("picture", ""),
                            registration_type = 3,
                            )
                return _user

    # -------------------------------------------------------------------------
    def call_api(self):
        api_return = urllib.urlopen("https://www.googleapis.com/oauth2/v1/userinfo?access_token=%s" % self.accessToken())
        user = json.loads(api_return.read())
        if user:
            return user
        else:
            self.session.token = None
            return None

# =============================================================================
class S3RoleMatrix(S3Method):
    """
        REST Method to manage ACLs for people on entities
        (Role Manager UI for organisation administrators)
    """

    controllers = Storage()

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Apply role manager
        """
        method = self.method
        manager = current.manager

        if method == "roles" and r.name == "person":
            output = self._roles(r, **attr)
        elif method == "users" and r.name in ("organisation", "office"):
            output = self._users(r, **attr)
        else:
            r.error(405, manager.ERROR.BAD_METHOD)

        if r.http == "GET" and method not in ("create", "update", "delete"):
            current.session.s3.cancel = r.url()
        return output

    # -------------------------------------------------------------------------
    def _roles(self, request, **kwargs):
        """
            In this view we have a person record and the orgadmin can select
            an organisation or office.

            @returns: a dict object for a view.
        """
        self.request = request
        self.kwargs = kwargs
        self.output = {}
        s3db = current.s3db
        db = current.db
        T = current.T

        current.response.view = "admin/manage_roles.html"
        self.output["title"] = T("User Roles")

        # Check we're logged in as an admin or org_admin
        # and fetch the realm
        realm = self.get_realm()

        # Get the users for this admin is allowed to edit roles
        users = s3db.pr_realm_users(realm)

        # This is the user account the roles will apply to
        user = self.get_user_by_pe_id(request.record.pe_id)
        if user:
            user.name = users.get(int(user.id), None)
        else:
            user.name = None
        self.output["user"] = user

        entities = s3db.pr_get_entities(pe_ids=realm,
                                        types=["org_organisation",
                                               "org_office"],
                                        group=True)

        # The entity is a pe_id and name for an organisation or office
        entity = Storage()
        entity.id = request.get_vars.get("entity", None)
        entity.name = None

        if entity.id:
            entity.id = int(entity.id)

            # Go through the entity groups to find the entity that matches the
            # id selected in the form
            for group, ents in entities.iteritems():
                if entity.id in ents.keys():
                    entity.name = ents[entity.id]
                    break

        # Take the grouped list of entities and create optgroups from it
        instance_type_nice = s3db.table("pr_pentity").instance_type.represent

        options = []
        for instance_type in entities:
            optgroup = OPTGROUP(_label=instance_type_nice(instance_type))
            items = [(n, i) for i, n in entities[instance_type].items()]
            items.sort()
            for name, pe_id in items:
                optgroup.append(OPTION(name, _value=pe_id))
            options.append(optgroup)

        # The form for selecting a user
        self.output["form"] = FORM(TABLE(TR(TD(LABEL("%s: " % T("Organization or Office"),
                                                     _for="entity"),
                                               _class="w2p_fl"),
                                            TD(SELECT(OPTION(""),
                                                      *options,
                                                      _name="entity",
                                                      value=entity.id),
                                               _class="w2p_fw")),
                                         TR(TD(),
                                            TD(INPUT(_type="submit",
                                                     _value=T("Select"))))),
                                   _method="GET")

        return self.process_forms(user, entity)

    # -------------------------------------------------------------------------
    def _users(self, request, **kwargs):
        """
            In this view we have a pr_pentity record of an organisation or office
            and the orgadmin can select a user account to edit the roles for.

            @returns: a dict object for a view.
        """
        self.request = request
        self.kwargs = kwargs
        self.output = {}
        s3db = current.s3db
        db = current.db
        T = current.T

        current.response.view = "admin/manage_roles.html"
        self.output["title"] = T("User Roles")

        # Check we're logged in as an admin or org_admin
        # and fetch the realm
        realm = self.get_realm()

        # Get the users for this admin is allowed to edit roles
        users = s3db.pr_realm_users(realm)

        # This is the user account the roles will apply to
        user = Storage()
        user.id = request.get_vars.get("user", None)
        if user.id:
            user.name = users.get(int(user.id), None)

        # We're access this method from an entity (org, office or group)
        # so we already have a record
        entity = Storage()
        entity.id = request.record.pe_id
        entity.name = s3db.pr_get_entities(pe_ids=[entity.id],
                                           types=["org_organisation",
                                                  "org_office"])[entity.id]
        self.output["entity"] = entity

        # Check that the orgadmin has permission to edit roles
        # for this entity
        if realm and entity.id not in realm:
            current.auth.permission.fail()

        # The form for selecting a user
        self.output["form"] = SQLFORM.factory(Field("user",
                                                    T("User"),
                                                    requires=IS_IN_SET(users),
                                                    default=user.id),
                                              _method="GET",
                                              submit_button="Select")

        return self.process_forms(user, entity)

    # -------------------------------------------------------------------------
    def get_realm(self):
        """
            Returns the realm (list of pe_ids) that this user can manage
            or raises a permission error if the user is not logged in
        """
        system_roles = current.auth.get_system_roles()
        ORG_ADMIN = system_roles.ORG_ADMIN
        ADMIN = system_roles.ADMIN

        if current.auth.user:
            realms = current.auth.user.realms
        else:
            # User is not logged in
            current.auth.permission.fail()

        # Get the realm from the current realms
        if ADMIN in realms:
            return realms[ADMIN]
        elif ORG_ADMIN in realms:
            return realms[ORG_ADMIN]
        else:
            # raise an error here - user is not permitted
            # to access the role matrix
            current.auth.permission.fail()

    # -------------------------------------------------------------------------
    def get_user_by_pe_id(self, pe_id):
        """
            Returns a dict with the id and name of the user that is linked
            to a pentity record.

            @type pe_id: int
            @param pe_id: The id of the pentity in the database.

            @todo: move this into AuthS3
        """
        s3db = current.s3db
        auth = current.auth

        utable = current.auth.settings.table_user
        ltable = current.s3db.pr_person_user

        if auth.settings.username:
            username = utable.username
        else:
            username = utable.email

        query = (ltable.pe_id == pe_id) & \
                (ltable.user_id == utable.id)
        record = current.db(query).select(utable.id, username).first()

        user = Storage()
        if record:
            user["id"] = record.id
            user["name"] = record[username]
        return user

    # -------------------------------------------------------------------------
    def get_modules(self):
        """
            This returns an OrderedDict of modules with their uid as the key,
            e.g., {hrm: "Human Resources",}
        """
        return current.deployment_settings.get_aaa_role_modules()

    # -------------------------------------------------------------------------
    def get_access_levels(self):
        """
            This returns an OrderedDict of access levels and their uid as
            the key, e.g., {reader: "Reader",}
        """
        return current.deployment_settings.get_aaa_access_levels()

    # -------------------------------------------------------------------------
    def get_matrix_options(self, module_uids, access_level_uids):
        """
            This fetches all the values required for populating the role
            matrix.

            @param module_uids: A list of strings. These are prefixes for
                                roles, e.g., ["project", "asset",]
            @param access_level_uids: A list of string. These are suffixes
                                      for roles, e.g., ["reader", "editor",]
        """
        options = []
        # for each module
        for module in module_uids:
            # The first value is for "None" access level
            row = [None,]

            # for each access level
            for access_level in access_level_uids:
                uid = "%s_%s" % (module, access_level) # combine the UIDs
                row.append(uid)

            options.append(row)

        return options

    # -------------------------------------------------------------------------
    def get_user_roles(self, user, entity, module_uids):
        """
            Returns the current roles for the user against the current entity.

            @type user: Storage()
            @param user: A Storage() object with "id" and "name" properties
            @type entity: Storage()
            @param entity: A Storage() object with "id" (pe_id) and
                           "name" (string) properties
            @type module_uids: list
            @param module_uids: A list of strings that are prefixes for roles
                                e.g., ["proj", "asset"]
        """

        # Get current memberships
        mtable = current.auth.settings.table_membership
        gtable = current.auth.settings.table_group
        query = (mtable.deleted != True) & \
                (mtable.user_id == user.id) & \
                (gtable.deleted != True) & \
                (mtable.group_id == gtable.id) & \
                (mtable.pe_id == entity.id)
        rows = current.db(query).select(gtable.uuid)

        # We only want roles that will be shown in the matrix
        values = {}
        for row in rows:
            role = row[gtable.uuid]
            module_uid = role.split("_", 1)[0]
            if module_uid in module_uids:
              field_name = "role_%s" % module_uid
              values[field_name] = role
        return values

    # -------------------------------------------------------------------------
    def role_form_factory(self,
                          user,
                          entity,
                          row_labels,
                          col_labels,
                          options,
                          groups):
        """
            Constructs the form for the role matrix

            @type user: Storage()
            @param user: A Storage() object with "id" and "name" properties
            @type entity: Storage()
            @param entity: A Storage() object with "id" (pe_id) and
                        "name" (string) properties
        """
        fields = []
        for idx, option_list in enumerate(options):
            name = "%s_%s" % ("role", groups[idx])
            field = self.role_field_factory(name, row_labels[idx], option_list)
            fields.append(field)

        form = SQLFORM.factory(*fields,
                               hidden=dict(user=user.id, entity=entity.id),
                               _method="POST")
        form.custom["matrix_access_level_labels"] = col_labels

        return form

    # -------------------------------------------------------------------------
    def role_field_factory(self, name, label, options):
        """
            Returns a Field object for a single row in the role matrix.

            @type name: String
            @param name: The name of the field e.g., "project_editor"
            @type label: String
            @param label: The label for this row in the matrix,
                          e.g., "Projects"
        """
        return Field(
            name,
            label=label,
            widget=lambda field,value: self.role_matrix_row(field, value),
            requires=IS_IN_SET(options)
        )

    # -------------------------------------------------------------------------
    @staticmethod
    def role_matrix_row(field, value, **attributes):
        """
            This is a custom widget that just returns a list of INPUT objects
        """
        table = SQLFORM.widgets.radio.widget(field, value,
                                             _class="test", **attributes)
        return [td.element("input") for td in table.elements("td")]

    # -------------------------------------------------------------------------
    def process_forms(self, user, entity):
        """
            Takes a user and an entity and returns a dictionary for the view

            @param user: A Storage() object with "id" and "name" properties
            @param entity: A Storage() object with "id" (pe_id) and
                        "name" (string) properties
        """
        if user.name and entity.name:
            if self.role_form_is_valid(user, entity):
                redirect(self.request.url())
            else:
                self.output["user"] = user
                self.output["entity"] = entity

        return self.output

    # -------------------------------------------------------------------------
    def role_form_is_valid(self, user, entity):
        """
            Takes user and entity objects and constructs the role matrix. If
            the role matrix form as been submitted, the values are tested and
            the result (True/False) is returned.

            @param user: A Storage() object with "id" and "name" properties
            @param entity: A Storage() object with "id" (pe_id) and
                        "name" (string) properties
        """
        T = current.T

        modules = self.get_modules()
        module_uids = modules.keys()
        row_labels = modules.values()

        access_levels = self.get_access_levels()
        access_level_uids = access_levels.keys()
        # Need "None" as a value for the no-access value
        col_labels = [T("None"),] + access_levels.values()

        options = self.get_matrix_options(module_uids, access_level_uids)

        # Fetch the current roles for this user
        user_roles = self.get_user_roles(user,
                                         entity,
                                         module_uids)

        # Build the role matrix form
        role_form = self.role_form_factory(user,
                                           entity,
                                           row_labels,
                                           col_labels,
                                           options,
                                           module_uids)

        # Set the values of the role matrix to the current roles
        role_form.vars.update(user_roles)

        # If the role matrix form has been submitted, test it's valid
        post_vars = self.request.post_vars
        if role_form.accepts(post_vars, current.session, keepvalues=True):
            before = user_roles.values()
            after = [role_uid for group, role_uid in role_form.vars.items()
                              if group[:5] == "role_"]
            self.update_roles(post_vars.user, post_vars.entity, before, after)
            current.session.confirmation = T("Roles updated")
            return True
        else:
            # The role matrix form is either invalid or hasn't been submitted
            # so we need to add it to show it again
            self.output["role_form"] = role_form
            return False

    # -------------------------------------------------------------------------
    def update_roles(self, user_id, entity_id, before, after):
        """
            Update the users roles on entity based on the selected roles
            in before and after
        """
        for role_uid in before:
            # If role_uid is not in after,
            # the access level has changed.
            if role_uid not in after:
                current.auth.s3_retract_role(user_id, role_uid, entity_id)

        for role_uid in after:
            # If the role_uid is not in before,
            # the access level has changed
            if role_uid != "None" and role_uid not in before:
                current.auth.s3_assign_role(user_id, role_uid, entity_id)

# END =========================================================================
