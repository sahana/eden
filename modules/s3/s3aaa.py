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
           "S3RoleManager"]

import datetime
import re

from gluon import *
from gluon.storage import Storage, Messages

from gluon.dal import Field, Row, Query, Set, Table, Expression
from gluon.sqlhtml import CheckboxesWidget, StringWidget
from gluon.tools import Auth, callback
from gluon.contrib.simplejson.ordered_dict import OrderedDict

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
                define_tables()
                login()
                register()
                profile()
                verify_email()
                requires_membership()

            - add:
                s3_has_role()
                s3_has_permission()
                s3_logged_in()
                s3_accessible_query()
                s3_impersonate()
                s3_register() callback
                s3_link_to_person()
                s3_verify_email_onaccept()
                s3_group_members()
                s3_user_to_person()
                s3_person_to_user()
                person_id()

            - language
            - utc_offset
            - organisation
            - @ToDo: Facility
    """

    # Configuration of UIDs for system roles
    S3_SYSTEM_ROLES = Storage(ADMIN = "ADMIN",
                              AUTHENTICATED = "AUTHENTICATED",
                              ANONYMOUS = "ANONYMOUS",
                              EDITOR = "EDITOR",
                              MAP_ADMIN = "MAP_ADMIN")

    def __init__(self):

        """ Initialise parent class & make any necessary modifications """

        Auth.__init__(self, current.db)

        self.settings.lock_keys = False
        self.settings.username_field = False
        self.settings.lock_keys = True
        self.messages.lock_keys = False
        self.messages.registration_pending_approval = "Account registered, however registration is still pending approval - please wait until confirmation received."
        self.messages.email_approver_failed = "Failed to send mail to Approver - see if you can notify them manually!"
        self.messages.email_verification_failed = "Unable to send verification email - either your email is invalid or our email server is down"
        self.messages.email_sent = "Verification Email sent - please check your email to validate. If you do not receive this email please check you junk email or spam filters"
        self.messages.email_verified = "Email verified - you can now login"
        self.messages.duplicate_email = "This email address is already in use"
        self.messages.registration_disabled = "Registration Disabled!"
        self.messages.registration_verifying = "You haven't yet Verified your account - please check your email"
        self.messages.label_organisation_id = "Organization"
        self.messages.label_site_id = "Facility"
        self.messages.label_utc_offset = "UTC Offset"
        self.messages.label_view_image = "View Image"
        self.messages.label_no_image = "No Image"
        self.messages.help_utc_offset = "The time difference between UTC and your timezone, specify as +HHMM for eastern or -HHMM for western timezones."
        self.messages.help_mobile_phone = "Entering a phone number is optional, but doing so allows you to subscribe to receive SMS messages."
        self.messages.help_organisation = "Entering an Organization is optional, but doing so directs you to the appropriate approver & means you automatically get the appropriate permissions."
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
        if current.deployment_settings.get_ui_camp():
            shelter = T("Camp")
        else:
            shelter = T("Shelter")
        self.org_site_types = Storage(
                                      cr_shelter = shelter,
                                      org_office = T("Office"),
                                      hms_hospital = T("Hospital"),
                                      #project_site = T("Project Site"),
                                      #fire_station = T("Fire Station"),
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
                    Field("image", "upload", autodelete=True,
                          represent = lambda image: image and \
                                        DIV(A(IMG(_src=URL(c="default", f="download",
                                                           args=image),
                                                  _height=60, _alt=self.messages.label_view_image),
                                                  _href=URL(c="default", f="download",
                                                            args=image))) or self.messages.label_no_image),
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
                    Field("image", "upload", autodelete=True,
                          represent = lambda image: image and \
                                        DIV(A(IMG(_src=URL(c="default", f="download",
                                                           args=image),
                                                  _height=60, _alt=self.messages.label_view_image),
                                                  _href=URL(c="default", f="download",
                                                            args=image))) or self.messages.label_no_image),
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

        if security_policy not in (1, 2, 3, 4, 5, 6, 7) and \
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
                self.set_roles()
                return user
        return False

    # -------------------------------------------------------------------------
    def set_roles(self):
        """
            Update session roles and pe_id for the current user
        """

        if self.user:
            db = current.db
            session = current.session

            table_user = self.settings.table_user
            table_membership = self.settings.table_membership
            user_id = self.user.id

            # Add the Roles to session.s3
            roles = []
            query = (table_membership.deleted != True) & \
                    (table_membership.user_id == user_id)
            rows = db(query).select(table_membership.group_id)
            session.s3.roles = [s.group_id for s in rows]

            # Set pe_id for current user
            ltable = current.s3db.pr_person_user
            if ltable is not None:
                query = (ltable.user_id == user_id)
                row = db(query).select(ltable.pe_id, limitby=(0, 1)).first()
                if row:
                    session.auth.user["pe_id"] = row.pe_id
        return

    # -------------------------------------------------------------------------
    def set_cookie(self):
        """
            Set a Cookie to the client browser so that we know this user has
            registered & so we should present them with a login form instead
            of a register form
        """

        response = current.response

        response.cookies["registered"] = "yes"
        response.cookies["registered"]["expires"] = 365 * 24 * 3600    # 1 year
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
        if "username" in table_user.fields:
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
        if next == DEFAULT:
            next = request.vars._next or self.settings.login_next
        if onvalidation == DEFAULT:
            onvalidation = self.settings.login_onvalidation
        if onaccept == DEFAULT:
            onaccept = self.settings.login_onaccept
        if log == DEFAULT:
            log = self.messages.login_log

        user = None # default

        # do we use our own login form, or from a central source?
        if self.settings.login_form == self:
            form = SQLFORM(
                table_user,
                fields=[username, passfield],
                hidden=dict(_next=request.vars._next),
                showid=self.settings.showid,
                submit_button=self.messages.submit_button,
                delete_label=self.messages.delete_label,
                )
            accepted_form = False
            if form.accepts(request.vars, session,
                            formname="login", dbio=False,
                            onvalidation=onvalidation):
                accepted_form = True
                # check for username in db
                query = (table_user[username] == form.vars[username])
                users = db(query).select()
                if users:
                    # user in db, check if registration pending or disabled
                    temp_user = users[0]
                    if temp_user.registration_key == "pending":
                        response.warning = self.messages.registration_pending
                        return form
                    elif temp_user.registration_key == "disabled":
                        response.error = self.messages.login_disabled
                        return form
                    elif temp_user.registration_key:
                        response.warning = \
                            self.messages.registration_verifying
                        return form
                    # try alternate logins 1st as these have the current version of the password
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
                        # alternates have failed, maybe because service inaccessible
                        if self.settings.login_methods[0] == self:
                            # try logging in locally using cached credentials
                            if temp_user[passfield] == form.vars.get(passfield, ""):
                                # success
                                user = temp_user
                else:
                    # user not in db
                    if not self.settings.alternate_requires_registration:
                        # we're allowed to auto-register users from external systems
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
                    # invalid login
                    session.error = self.messages.invalid_login
                    redirect(self.url(args=request.args,
                                      vars=request.get_vars))
        else:
            # use a central authentication server
            cas = self.settings.login_form
            cas_user = cas.get_user()
            if cas_user:
                cas_user[passfield] = None
                user = self.get_or_create_user(cas_user)
            elif hasattr(cas, "login_form"):
                return cas.login_form()
            else:
                # we need to pass through login again before going on
                next = "%s?_next=%s" % (URL(r=request), next)
                redirect(cas.login_url(next))

        # process authenticated users
        if user:
            user = Storage(table_user._filter_fields(user, id=True))
            # If the user hasn't set a personal UTC offset,
            # then read the UTC offset from the form:
            if not user.utc_offset:
                user.utc_offset = session.s3.utc_offset
            session.auth = Storage(user=user, last_visit=request.now,
                                   expiration=self.settings.expiration)
            self.user = user
            self.set_roles()
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

        # how to continue
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
    def s3_lookup_org_role(self, organisation_id):
        """
            Lookup the Organisation Access Role from the ID of the Organisation
        """

        if not organisation_id:
            return None

        db = current.db
        s3db = current.s3db
        table = s3db.org_organisation
        query = (table.id == organisation_id)
        org = db(query).select(table.owned_by_organisation).first()
        if org:
            return org.owned_by_organisation

        return None

    # -------------------------------------------------------------------------
    def s3_lookup_site_role(self, site_id):
        """
            Lookup the Facility Access Role from the ID of the Facility
        """

        if not site_id:
            return None

        db = current.db
        s3db = current.s3db
        table = s3db.org_site
        query = (table.id == site_id)
        site = db(query).select(table.instance_type).first()
        if site:
            instance_type = site.instance_type
            itable = db[instance_type]
            query = (itable.site_id == site_id)
            _site = db(query).select(itable.owned_by_facility).first()
            if _site:
                return _site.owned_by_facility

        return None

    # -------------------------------------------------------------------------
    def s3_impersonate(self, user_id):
        """
            S3 framework function

            Designed to be used within tasks, which are run in a separate request
            & hence don't have access to current.auth

            @param user_id: auth.user.id
        """

        session = current.session
        db = current.db

        if not user_id:
            # Anonymous
            return None

        table_user = self.settings.table_user
        user = db(table_user.id == user_id).select(limitby=(0, 1)).first()

        if not user:
            # Invalid user ID
            return False

        roles = []
        table_membership = self.settings.table_membership
        memberships = db(table_membership.user_id == user.id).select(
                                                    table_membership.group_id)
        roles = [m.group_id for m in memberships]
        if session.s3.system_roles.ANONYMOUS:
            roles.append(session.s3.system_roles.ANONYMOUS)

        session.s3.roles = roles

        # Set the language from the Profile
        language = user.language
        current.T.force(language)
        current.session.s3.language = language

        user = Storage(table_user._filter_fields(user, id=True))

        # Use this user
        self.user = user

        return user

    # -------------------------------------------------------------------------
    def s3_register(self, form):
        """
            S3 framework function

            Designed to be used as an onaccept callback for register()

            Whenever someone registers, it:
                - adds them to the 'Authenticated' role
                - adds their name to the Person Registry
                - creates an HRM record
                - adds them to the Org_x Access role
        """

        db = current.db
        manager = current.manager
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        user_id = form.vars.id
        if not user_id:
            return None

        # Add to 'Authenticated' role
        authenticated = self.id_group("Authenticated")
        self.add_membership(authenticated, user_id)

        # Link to organisation, lookup org role
        organisation_id = self.s3_link_to_organisation(form.vars)
        if organisation_id:
            owned_by_organisation = self.s3_lookup_org_role(organisation_id)
        else:
            owned_by_organisation = None

        # For admin/user/create, lookup facility role
        site_id = form.vars.get("site_id", None)
        if site_id:
            owned_by_facility = self.s3_lookup_site_role(site_id)
        else:
            owned_by_facility = None

        # Add to Person Registry and Email/Mobile to pr_contact
        person_id = self.s3_link_to_person(form.vars, # user
                                           owned_by_organisation,
                                           owned_by_facility)

        htable = s3db.table("hrm_human_resource")
        if htable and organisation_id:

            # Create an HRM entry, if one doesn't already exist
            query = (htable.person_id == person_id) & \
                    (htable.organisation_id == organisation_id)
            row = db(query).select(htable.id, limitby=(0, 1)).first()

            if not row:
                id = htable.insert(person_id=person_id,
                                   organisation_id=organisation_id,
                                   owned_by_user=user_id,
                                   owned_by_organisation=owned_by_organisation,
                                   owned_by_facility=owned_by_facility)
                record = Storage(id=id)
                manager.model.update_super(htable, record)

            if owned_by_organisation:
                # Add user to the Org Access Role
                table = self.settings.table_membership
                query = (table.deleted != True) & \
                        (table.user_id == user_id) & \
                        (table.group_id == owned_by_organisation)
                if not db(query).select(table.id,
                                        limitby=(0, 1)).first():
                    table.insert(user_id=user_id,
                                 group_id=owned_by_organisation)

            if owned_by_facility:
                # Add user to the Site Access Role
                table = self.settings.table_membership
                query = (table.deleted != True) & \
                        (table.user_id == user_id) & \
                        (table.group_id == owned_by_facility)
                if not db(query).select(table.id,
                                        limitby=(0, 1)).first():
                    table.insert(user_id=user_id,
                                 group_id=owned_by_facility)

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

        organisation_id = user.organisation_id
        if not organisation_id:
            otable = s3db.org_organisation
            name = user.get("organisation_name", None)
            acronym = user.get("organisation_acronym", None)
            if name:
                # Create new organisation
                organisation_id = otable.insert(name=name,
                                                acronym=acronym)
                # Update the super-entities
                record = Storage(id=organisation_id)
                manager.model.update_super(otable, record)
                # Set record ownership
                self.s3_set_record_owner(otable, organisation_id)
                user.organisation_id = organisation_id
                # Update user record
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
                          owned_by_organisation=None,
                          owned_by_facility=None):
        """
            Links user accounts to person registry entries

            @param user: the user record
            @param owned_by_organisation: the role of the owner organisation
            @param owned_by_facility: the role of the owner facility

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
                            owned_by_organisation=owned_by_organisation,
                            owned_by_facility=owned_by_facility)

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
                                          ptable.pe_id).first()

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
                    new_id = ptable.insert(pe_id = pe_id,
                                           track_id = track_id,
                                           first_name = first_name,
                                           last_name = last_name,
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

        # User own their own HRM records
        query = (htable.person_id == person_id)
        db(query).update(owned_by_user=user_id)

        query &= ((htable.status == 1) &
                  (htable.deleted != True))
        rows = db(query).select(htable.owned_by_organisation,
                                htable.owned_by_facility)
        org_roles = []
        fac_roles = []
        for row in rows:
            org_role = row.owned_by_organisation
            if org_role and org_role not in org_roles:
                query = (mtable.deleted != True) & \
                        (mtable.user_id == user_id) & \
                        (mtable.group_id == org_role)
                if not db(query).select(limitby=(0, 1)).first():
                    org_roles.append(dict(user_id=user_id,
                                          group_id=org_role))
            fac_role = row.owned_by_facility
            if fac_role and fac_role not in fac_roles:
                query = (mtable.deleted != True) & \
                        (mtable.user_id == user_id) & \
                        (mtable.group_id == fac_role)
                if not db(query).select(limitby=(0, 1)).first():
                    fac_roles.append(dict(user_id=user_id,
                                          group_id=fac_role))
        if org_roles:
            mtable.bulk_insert(org_roles)
        if fac_roles:
            mtable.bulk_insert(fac_roles)

    # -------------------------------------------------------------------------
    def s3_logged_in(self):
        """
            Check whether the user is currently logged-in
            - tries Basic if not
        """

        if self.override:
            return True

        session = current.session
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

            Caution: do NOT cache the result, otherwise a newly installed
            system would be completely open during the caching period!
        """

        session = current.session

        try:
            if session.s3.system_roles:
                return session.s3.system_roles
        except:
            pass

        db = current.db
        rtable = self.settings.table_group
        if rtable is not None:
            system_roles = self.S3_SYSTEM_ROLES
            query = (rtable.deleted != True) & \
                    rtable.uuid.belongs(system_roles.values())
            rows = db(query).select(rtable.id, rtable.uuid)
            sr = Storage([(role.uuid, role.id) for role in rows])
        else:
            sr = Storage([(uid, None) for uid in self.S3_SYSTEM_ROLES])

        session.s3.system_roles = sr
        return sr

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
                self.s3_update_acl(role_id, **acl)

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
    def resolve_role_ids(self, roles):
        """
            Resolve role UIDs

            @param roles: list of role IDs or UIDs (or mixed)
        """

        if not isinstance(roles, (list, tuple)):
            roles = [roles]

        role_ids = []
        role_uids = []
        for role_id in roles:
            if isinstance(role_id, str) and not role_id.isdigit():
                role_uids.append(role_id)
            else:
                _id = int(role_id)
                if _id not in role_ids:
                    role_ids.append(_id)
        if role_uids:
            rtable = self.settings.table_group
            query = (rtable.deleted != True) & \
                    (rtable.uuid.belongs(role_uids))
            rows = db(query).select(rtable.id)
            role_ids += [r.id for r in rows if r.id not in role_ids]

        return role_ids

    # -------------------------------------------------------------------------
    def s3_assign_role(self, user_id, role_id):
        """
            Assigns a role to a user

            @param user_id: the record ID of the user account
            @param role_id: the record ID(s)/UID(s) of the role

            @note: strings or lists of strings are assumed to be
                   role UIDs
        """

        db = current.db
        rtable = self.settings.table_group
        mtable = self.settings.table_membership

        query = (rtable.deleted != True)
        if isinstance(role_id, (list, tuple)):
            if isinstance(role_id[0], str):
                query &= (rtable.uuid.belongs(role_id))
            else:
                roles = role_id
        elif isinstance(role_id, str):
            query &= (rtable.uuid == role_id)
        else:
            roles = [role_id]
        if query is not None:
            roles = db(query).select(rtable.id)
            roles = [r.id for r in roles]

        query = (mtable.deleted != True) & \
                (mtable.user_id == user_id) & \
                (mtable.group_id.belongs(roles))
        assigned = db(query).select(mtable.group_id)
        assigned_roles = [r.group_id for r in assigned]

        for role in roles:
            if role not in assigned_roles:
                mtable.insert(user_id=user_id, group_id=role)

    # -------------------------------------------------------------------------
    def s3_retract_role(self, user_id, role_id):
        """
            Removes a role assignment from a user account

            @param user_id: the record ID of the user account
            @param role_id: the record ID(s)/UID(s) of the role

            @note: strings or lists of strings are assumed to be
                   role UIDs
        """

        if not role_id:
            return

        db = current.db
        rtable = self.settings.table_group
        mtable = self.settings.table_membership

        query = (rtable.deleted != True)
        if isinstance(role_id, (list, tuple)):
            if isinstance(role_id[0], str):
                query &= (rtable.uuid.belongs(role_id))
            else:
                roles = role_id
        elif isinstance(role_id, str):
            query &= (rtable.uuid == role_id)
        else:
            roles = [role_id]
        if query is not None:
            roles = db(query).select(rtable.id)
            roles = [r.id for r in roles]

        query = (mtable.deleted != True) & \
                (mtable.user_id == user_id) & \
                (mtable.group_id.belongs(roles))
        db(query).update(deleted=True)

    # -------------------------------------------------------------------------
    def s3_has_role(self, role):
        """
            Check whether the currently logged-in user has a role

            @param role: the record ID or UID of the role
        """

        if self.override:
            return True

        db = current.db
        session = current.session
        if not session.s3:
            return False

        # Trigger HTTP basic auth
        self.s3_logged_in()
        roles = session.s3.roles
        if not roles:
            return False

        system_roles = session.s3.system_roles
        if system_roles and system_roles.ADMIN in roles:
            # Administrators have all roles
            return True

        if isinstance(role, str):
            if role.isdigit():
                role = int(role)
            else:
                rtable = self.settings.table_group
                query = (rtable.deleted != True) & \
                        (rtable.uuid == role)
                row = db(query).select(rtable.id, limitby=(0, 1)).first()
                if row:
                    role = row.id
                else:
                    return False

        return role in session.s3.roles

    # -------------------------------------------------------------------------
    # ACL management
    # -------------------------------------------------------------------------
    def s3_update_acls(self, role, *acls):
        """
            Wrapper for s3_update_acl to allow batch updating
        """

        for acl in acls:
            self.s3_update_acl(role, **acl)

    # -------------------------------------------------------------------------
    def s3_update_acl(self, role,
                      c=None, f=None, t=None, oacl=None, uacl=None,
                      organisation=None, facility=None):
        """
            Back-end method to update an ACL
        """

        ALL = "all"

        all_organisations = organisation == ALL
        if all_organisations:
            organisation = None

        all_facilities = facility == ALL
        if all_facilities:
            facility = None

        table = self.permission.table
        if not table:
            # ACLs not relevant to this security policy
            return None

        if c is None and f is None and t is None:
            return None

        if t is not None:
            c = f = None

        if uacl is None:
            uacl = self.permission.NONE
        if oacl is None:
            oacl = uacl

        if role:
            query = ((table.group_id == role) & \
                     (table.controller == c) & \
                     (table.function == f) & \
                     (table.tablename == t))
            record = current.db(query).select(table.id, limitby=(0, 1)).first()
            acl = dict(deleted=False,
                       group_id=role,
                       controller=c,
                       function=f,
                       tablename=t,
                       oacl=oacl,
                       uacl=uacl,
                       all_organisations=all_organisations,
                       organisation=organisation,
                       all_facilities=all_facilities,
                       facility=facility)
            if record:
                success = record.update_record(**acl)
            else:
                success = table.insert(**acl)

        return success

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------
    def s3_group_members(self, group_id):
        """
            Get a list of members of a group

            @param group_id: the group record ID
            @returns: a list of the user_ids for members of a group
        """

        membership = self.settings.table_membership
        query = (membership.deleted != True) & \
                (membership.group_id == group_id)
        members = current.db(query).select(membership.user_id)
        return [member.user_id for member in members]


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
            Get the person record ID for the current logged-in user
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
    def s3_has_permission(self, method, table, record_id = 0):
        """
            S3 framework function to define whether a user can access a record
            in manner "method". Designed to be called from the RESTlike
            controller.

            @param table: the table or tablename
        """

        if self.override:
            return True

        db = current.db
        session = current.session

        if not hasattr(table, "_tablename"):
            s3db = current.s3db
            table = s3db[table]

        if session.s3.security_policy == 1:
            # Simple policy
            # Anonymous users can Read.
            if method == "read":
                authorised = True
            else:
                # Authentication required for Create/Update/Delete.
                authorised = self.s3_logged_in()

        elif session.s3.security_policy == 2:
            # Editor policy
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
                authorised = self.s3_has_role("Editor")
                if not authorised and self.user and "owned_by_user" in table:
                    # Creator of Record is allowed to Edit
                    query = (table.id == record_id)
                    record = db(query).select(table.owned_by_user,
                                              limitby=(0, 1)).first()
                    if record and self.user.id == record.owned_by_user:
                        authorised = True

        elif session.s3.security_policy == 3:
            # Controller ACLs
            self.permission.use_cacls = True
            self.permission.use_facls = False
            self.permission.use_tacls = False
            authorised = self.permission.has_permission(table,
                                                        record=record_id,
                                                        method=method)

        elif session.s3.security_policy == 4:
            # Controller+Function ACLs
            self.permission.use_cacls = True
            self.permission.use_facls = True
            self.permission.use_tacls = False
            authorised = self.permission.has_permission(table,
                                                        record=record_id,
                                                        method=method)

        elif session.s3.security_policy >= 5:
            # Controller+Function+Table ACLs
            self.permission.use_cacls = True
            self.permission.use_facls = True
            self.permission.use_tacls = True
            authorised = self.permission.has_permission(table,
                                                        record=record_id,
                                                        method=method)

        else:
            # Full policy
            if self.s3_logged_in():
                # Administrators are always authorised
                if self.s3_has_role(1):
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
    def s3_accessible_query(self, method, table):
        """
            Returns a query with all accessible records for the currently
            logged-in user

            @note: This method does not work on GAE because it uses JOIN and IN
        """

        if self.override:
            return table.id > 0

        db = current.db
        session = current.session
        T = current.T

        policy = session.s3.security_policy

        if policy == 1:
            # "simple" security policy: show all records
            return table.id > 0
        elif policy == 2:
            # "editor" security policy: show all records
            return table.id > 0
        elif policy in (3, 4, 5, 6, 7):
            # ACLs: use S3Permission method
            query = self.permission.accessible_query(table, method)
            return query

        # "Full" security policy
        if self.s3_has_role(1):
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
    def s3_has_membership(self, group_id=None, user_id=None, role=None):
        """
            Checks if user is member of group_id or role

            Extends Web2Py's requires_membership() to add new functionality:
                - Custom Flash style
                - Uses s3_has_role()
        """

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

                if not self.s3_has_role(role) and not self.s3_has_role(1):
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

    # -------------------------------------------------------------------------
    def s3_session_owns(self, table, record_id):
        """
            Checks whether the current session owns a record

            @param table: the table or table name
            @param record_id: the record ID
        """

        if hasattr(table, "_tablename"):
            table = table._tablename
        if not self.user:
            try:
                records = current.session.owned_records.get(table, [])
            except:
                records = []
            if str(record_id) in records:
                return True
        return False

    # -------------------------------------------------------------------------
    def s3_set_record_owner(self, table, record):
        """
            Set the owner organisation and facility for a record

            @param table: the table or table name
            @param record: the record (as row) or record ID
        """

        db = current.db
        s3db = current.s3db
        manager = current.manager

        site_types = self.org_site_types

        OWNED_BY_ORG = "owned_by_organisation"
        OWNED_BY_FAC = "owned_by_facility"
        ORG_ID = "organisation_id"
        FAC_ID = "site_id"
        ORG_PREFIX = "Org_%s"
        FAC_PREFIX = "Fac_%s"
        ORG_TABLENAME = "org_organisation"
        FAC_TABLENAME = "org_site"
        NAME = "name"

        org_table = s3db[ORG_TABLENAME]
        fac_table = s3db[FAC_TABLENAME]
        grp_table = self.settings.table_group

        # Get the table
        if isinstance(table, str):
            table = s3db[table]
        tablename = table._tablename
        _id = table._id.name

        # Which fields are available?
        fields = [table._id.name,
                  NAME,
                  ORG_ID,
                  FAC_ID,
                  OWNED_BY_ORG,
                  OWNED_BY_FAC]
        fields = [table[f] for f in fields if f in table.fields]

        # Get the record
        if not isinstance(record, Row):
            record_id = record
            record = db(table._id == record_id).select(limitby=(0, 1),
                                                       *fields).first()
        else:
            if table._id.name in record:
                record_id = record[table._id.name]
            else:
                record_id = None
            missing = [f for f in fields if f not in record]
            if missing:
                if record_id:
                    query = table._id == record_id
                    record = db(query).select(limitby=(0, 1),
                                              *fields).first()
                else:
                    record = None
        if not record:
            # Raise an exception here?
            return

        # Get the organisation ID
        org_role = None
        if tablename == ORG_TABLENAME:
            organisation_id = record[_id]
            if OWNED_BY_ORG in record:
                org_role = record[OWNED_BY_ORG]
            if not org_role:
                # Create a new org_role
                uuid = ORG_PREFIX % organisation_id
                if NAME in table:
                    name = record[NAME]
                else:
                    name = uuid
                role = Storage(uuid=uuid,
                               deleted=False,
                               hidden=False,
                               system=True,
                               protected=True,
                               role="%s (Organisation)" % name,
                               description="All Staff of Organization %s" % name)
                query = (grp_table.uuid == role.uuid) | \
                        (grp_table.role == role.role)
                record =  db(query).select(grp_table.id,
                                           limitby=(0, 1)).first()
                if not record:
                    org_role = grp_table.insert(**role)
                else:
                    record.update_record(**role)
                    org_role = record.id
        elif ORG_ID in table:
            organisation_id = record[ORG_ID]
            # Get the org_role from the organisation
            if organisation_id:
                query = org_table.id == organisation_id
                organisation = db(query).select(org_table[OWNED_BY_ORG],
                                                limitby=(0, 1)).first()
                if organisation:
                    org_role = organisation[OWNED_BY_ORG]

        # Get the facility ID
        fac_role = None
        if tablename in site_types:
            site_id = record[FAC_ID]
            if OWNED_BY_FAC in record:
                fac_role = record[OWNED_BY_FAC]
            if not fac_role:
                # Create a new fac_role
                uuid = FAC_PREFIX % site_id
                if NAME in table:
                    name = record[NAME]
                else:
                    name = uuid
                role = Storage(uuid=uuid,
                               deleted=False,
                               hidden=False,
                               system=True,
                               protected=True,
                               role="%s (Facility)" % name,
                               description="All Staff of Facility %s" % name)
                query = (grp_table.uuid == role.uuid) | \
                        (grp_table.role == role.role)
                record =  db(query).select(grp_table.id,
                                           limitby=(0, 1)).first()
                if not record:
                    fac_role = grp_table.insert(**role)
                else:
                    record.update_record(**role)
                    fac_role = record.id
        elif FAC_ID in table:
            # Get the fac_role from the site
            site_id = record[FAC_ID]
            if site_id:
                query = fac_table[FAC_ID] == site_id
                site = db(query).select(fac_table.instance_type,
                                        fac_table.uuid,
                                        limitby=(0, 1)).first()
                if site:
                    inst_table = s3db[site.instance_type]
                    query = inst_table.uuid == site.uuid
                    facility = db(query).select(inst_table[OWNED_BY_FAC],
                                                limitby=(0, 1)).first()
                    if facility:
                        fac_role = facility[OWNED_BY_FAC]

        # Update the record as necessary
        data = Storage()
        if org_role and OWNED_BY_ORG in table:
            data[OWNED_BY_ORG] = org_role
        if fac_role and OWNED_BY_FAC in table:
            data[OWNED_BY_FAC] = fac_role
        if data and hasattr(record, "update_record"):
            record.update_record(**data)
        elif data and record_id:
            db(table._id == record_id).update(**data)

        return

# =============================================================================

class S3Permission(object):
    """
        S3 Class to handle permissions

        @author: Dominic König <dominic@aidiq.com>
    """

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
    METHODS = Storage(
        create = CREATE,
        read = READ,
        update = UPDATE,
        delete = DELETE)

    # Policy helpers
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

            @param tablename: the name for the permissions table
        """

        # Instantiated once per request, but before Auth tables
        # are defined and authentication is checked, thus no use
        # to check permissions in the constructor

        # Auth
        self.auth = auth

        # Deployment settings
        settings = current.deployment_settings
        self.policy = settings.get_security_policy()

        # Which level of granularity do we want?
        self.use_cacls = self.policy in (3, 4, 5, 6, 7) # Controller ACLs
        self.use_facls = self.policy in (4, 5, 6, 7)    # Function ACLs
        self.use_tacls = self.policy in (5, 6, 7)       # Table ACLs
        self.org_roles = self.policy in (6, 7)          # OrgAuth
        self.modules = settings.modules

        # If a large number of roles in the system turnes into a bottleneck
        # in policies 6 and 7, then we could reduce the number of roles in
        # subsequent queries; this would though add another query (or even two
        # more queries) to the request, so the hypothetic performance gain
        # should first be confirmed by tests:
        #if self.policy in (6, 7):
            #gtable = auth.settings.table_group
            #org_roles = current.db(gtable.uid.like("Org_%")).select(gtable.id)
            #self.org_roles = [r.id for r in org_roles]
        #else:
            #self.org_roles = []
        #if self.policy == 7:
            #gtable = auth.settings.table_group
            #fac_roles = current.db(gtable.uid.like("Fac_%")).select(gtable.id)
            #self.fac_roles = [r.id for r in fac_roles]
        #else:
            #self.fac_roles = []

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
                            Field("oacl", "integer", default=self.ALL),
                            Field("uacl", "integer", default=self.READ),
                            # Only apply to records owned by this
                            # organisation role (policy 6 only):
                            Field("all_organisations", "boolean",
                                  default=False),
                            Field("organisation",
                                  table_group,
                                  requires = IS_NULL_OR(IS_IN_DB(
                                                db, table_group.id))),
                            # Only apply to records owned by this
                            # facility role (policy 7 only):
                            Field("all_facilities", "boolean",
                                  default=False),
                            Field("facility",
                                  table_group,
                                  requires = IS_NULL_OR(IS_IN_DB(
                                                db, table_group.id))),
                            migrate=migrate,
                            fake_migrate=fake_migrate,
                            *(s3_uid()+s3_timestamp()+s3_deletion_status()))


    # -------------------------------------------------------------------------
    def __call__(self,
                 c=None,
                 f=None,
                 table=None,
                 record=None):
        """
            Get the ACL for the current user for a path

            @param c: the controller name (falls back request.controller)
            @param f: the function name (falls back to request.function)
            @param table: the table
            @param record: the record ID (or the Row if already loaded)

            @note: if passing a Row, it must contain all available ownership
                   fields (id, owned_by_user, owned_by_role), otherwise the
                   record will be re-loaded by this function
        """

        _debug("auth.permission(c=%s, f=%s, table=%s, record=%s)" %
                   (c, f, table, record))

        t = self.table # Permissions table
        auth = self.auth
        sr = auth.get_system_roles()

        if record == 0:
            record = None

        # Get user roles, check logged_in to trigger HTTPBasicAuth
        if not auth.s3_logged_in():
            roles = [sr.ANONYMOUS]
        else:
            roles = [sr.AUTHENTICATED]
        if current.session.s3 is not None:
            roles = current.session.s3.roles or roles
        if not self.use_cacls:
            # Fall back to simple authorization
            _debug("Simple authorization")
            if auth.s3_logged_in():
                _debug("acl=%04x" % self.ALL)
                return self.ALL
            else:
                _debug("acl=%04x" % self.READ)
                return self.READ
        if sr.ADMIN in roles:
            _debug("Administrator, acl=%04x" % self.ALL)
            return self.ALL

        # Fall back to current request
        c = c or self.controller
        f = f or self.function

        # Do we need to check the owner role (i.e. table+record given)?
        is_owner = False
        require_org = require_fac = None
        if table is not None and record is not None:
            owner_role, owner_user, owner_org, owner_fac = \
                self.get_owners(table, record)
            is_owner = self.is_owner(table, None,
                                     owner_role=owner_role,
                                     owner_user=owner_user,
                                     owner_org=owner_org,
                                     owner_fac=owner_fac)
            if self.policy == 6:
                require_org = owner_org
                require_fac = None
            elif self.policy == 7:
                require_org = owner_org
                require_fac = owner_fac

        # Get the applicable ACLs
        page_acl = self.page_acl(c=c, f=f,
                                 require_org=require_org,
                                 require_fac=require_fac)
        if table is None or not self.use_tacls:
            acl = page_acl
        else:
            if sr.EDITOR in roles:
                table_acl = (self.ALL, self.ALL)
            else:
                table_acl = self.table_acl(table=table,
                                           c=c,
                                           default=page_acl,
                                           require_org=require_org,
                                           require_fac=require_fac)
            acl = self.most_restrictive((page_acl, table_acl))

        # Decide which ACL to use for this case
        if acl[0] == self.NONE and acl[1] == self.NONE:
            # No table access at all
            acl = self.NONE
        elif record is None:
            # No record specified, return most permissive ACL
            acl = (acl[0] & ~self.CREATE) | acl[1]
        else:
            # ACL based on ownership
            acl = is_owner and (acl[0] | acl[1]) or acl[1]

        _debug("acl=%04x" % acl)
        return acl

    # -------------------------------------------------------------------------
    def page_acl(self, c=None, f=None,
                 require_org=None,
                 require_fac=None):
        """
            Get the ACL for a page

            @param c: the controller (falls back to current request)
            @param f: the function (falls back to current request)

            @returns: tuple of (ACL for owned resources, ACL for all resources)
        """

        session = current.session
        policy = self.policy
        t = self.table
        sr = self.auth.get_system_roles()
        most_permissive = self.most_permissive

        roles = []
        if session.s3 is not None:
            roles = session.s3.roles or []
        if sr.ADMIN in roles:
            # Admin always has rights
            return (self.ALL, self.ALL)

        c = c or self.controller
        f = f or self.function

        page = "%s/%s" % (c, f)
        if page in self.unrestricted_pages:
            page_acl = (self.ALL, self.ALL)
        elif c not in self.modules or \
             c in self.modules and not self.modules[c].restricted or \
             not self.use_cacls:
            # Controller is not restricted => simple authorization
            if self.auth.s3_logged_in():
                page_acl = (self.ALL, self.ALL)
            else:
                page_acl = (self.READ, self.READ)
        else:
            # Lookup cached result
            page_acl = self.page_acls.get((page,
                                           require_org,
                                           require_fac), None)

        if page_acl is None:
            page_acl = (self.NONE, self.NONE) # default
            q = ((t.deleted != True) & \
                 (t.controller == c) & \
                 ((t.function == f) | (t.function == None)))
            if roles:
                query = (t.group_id.belongs(roles)) & q
            else:
                query = (t.group_id == None) & q
            # Additional restrictions in OrgAuth
            if policy in (6, 7) and require_org:
                field = t.organisation
                query &= ((t.all_organisations == True) | \
                          (field == require_org) | (field == None))
            if policy == 7 and require_fac:
                field = t.facility
                query &= ((t.all_facilities == True) | \
                          (field == require_fac) | (field == None))
            rows = current.db(query).select()
            if rows:
                # ACLs found, check for function-specific
                controller_acl = []
                function_acl = []
                for row in rows:
                    if not row.function:
                        controller_acl += [(row.oacl, row.uacl)]
                    else:
                        function_acl += [(row.oacl, row.uacl)]
                # Function-specific ACL overrides Controller ACL
                if function_acl and self.use_facls:
                    page_acl = most_permissive(function_acl)
                elif controller_acl:
                    page_acl = most_permissive(controller_acl)

            # Remember this result
            self.page_acls.update({(page,
                                    require_org,
                                    require_fac): page_acl})

        return page_acl

    # -------------------------------------------------------------------------
    def table_acl(self, table=None, c=None, default=None,
                  require_org=None,
                  require_fac=None):
        """
            Get the ACL for a table

            @param table: the table
            @param c: the controller (falls back to current request)
            @param default: ACL to apply if no specific table ACL is found
            @returns: tuple of (ACL for owned resources, ACL for all resources)
        """
        if table is None or not self.use_tacls:
            return self.page_acl(c=c)

        policy = self.policy
        t = self.table
        sr = self.auth.get_system_roles()

        roles = []
        if current.session.s3 is not None:
            roles = current.session.s3.roles or []
        if sr.ADMIN in roles:
            # Admin always has rights
            return (self.ALL, self.ALL)

        c = c or self.controller

        if default is None:
            if self.auth.s3_logged_in():
                default = (self.ALL, self.ALL)
            else:
                default = (self.READ, self.READ)

        # Already loaded?
        if hasattr(table, "_tablename"):
            tablename = table._tablename
        else:
            tablename = table
        table_acl = self.table_acls.get((tablename,
                                         require_org,
                                         require_fac), None)

        if table_acl is None:
            q = ((t.deleted != True) & \
                 (t.tablename == tablename) &
                 ((t.controller == c) | (t.controller == None)))
            if roles:
                query = (t.group_id.belongs(roles)) & q
            else:
                query = (t.group_id == None) & q
            # Additional restrictions in OrgAuth
            if policy in (6, 7) and require_org:
                field = t.organisation
                query &= ((t.all_organisations == True) | \
                          (field == require_org) | (field == None))
            if policy == 7 and require_fac:
                field = t.facility
                query &= ((t.all_facilities == True) | \
                          (field == require_fac) | (field == None))
            rows = current.db(query).select()
            table_acl = [(r.oacl, r.uacl) for r in rows]
            if table_acl:
                # ACL found, apply most permissive role
                table_acl = self.most_permissive(table_acl)
            else:
                # No ACL found for any of the roles, fall back to default
                table_acl = default

            # Remember this result
            self.table_acls.update({(tablename,
                                     require_org,
                                     require_fac): table_acl})
        return table_acl

    # -------------------------------------------------------------------------
    def get_owners(self, table, record):
        """
            Get the organisation/facility/group/user owning a record

            @param table: the table
            @param record: the record ID (or the Row, if already loaded)
        """

        owner_org = None
        owner_fac = None
        owner_role = None
        owner_user = None

        record_id = None

        # Check which ownership fields the table defines
        ownership_fields = ("owned_by_user",
                            "owned_by_role",
                            "owned_by_organisation",
                            "owned_by_facility")
        fields = [f for f in ownership_fields if f in table.fields]
        if not fields:
            # Ownership is not defined for this table
            return (None, None, None, None)

        if isinstance(record, Row):
            # Check if all necessary fields are present
            missing = [f for f in fields if f not in record]
            if missing:
                # Have to reload the record :(
                if table._id.name in record:
                    record_id = record[table._id.name]
                record = None
        else:
            # Record ID given
            record_id = record
            record = None

        if not record and record_id:
            # Get the record
            fs = [table[f] for f in fields] + [table.id]
            query = (table._id == record_id)
            record = current.db(query).select(limitby=(0, 1), *fs).first()
        if not record:
            # Record does not exist
            return (None, None, None, None)

        if "owned_by_role" in record:
            owner_role = record["owned_by_role"]
        if "owned_by_user" in record:
            owner_user = record["owned_by_user"]
        if "owned_by_organisation" in record:
            owner_org = record["owned_by_organisation"]
        if "owned_by_facility" in record:
            owner_fac = record["owned_by_facility"]
        return (owner_role, owner_user, owner_org, owner_fac)

    # -------------------------------------------------------------------------
    def is_owner(self, table, record,
                 owner_role=None,
                 owner_user=None,
                 owner_org=None,
                 owner_fac=None):
        """
            Establish the ownership of a record

            @param table: the table
            @param record: the record ID (or the Row if already loaded)
            @param owner_role: owner_role of the record (if already known)
            @param owner_user: owner_user of the record (if already known)
            @param owner_org: owner_org of the record (if already known)
            @param owner_fac: owner_fac of the record (if already known)

            @note: if passing a Row, it must contain all available ownership
                   fields (id, owned_by_user, owned_by_role), otherwise the
                   record will be re-loaded by this function
        """

        user_id = None
        roles = []
        sr = self.auth.get_system_roles()

        if self.auth.user is not None:
            user_id = self.auth.user.id
        if current.session.s3 is not None:
            roles = current.session.s3.roles or []

        if not user_id and not roles:
            return False
        elif sr.ADMIN in roles:
            # Admin owns all records
            return True
        elif record:
            owner_role, owner_user, owner_org, owner_fac = \
                self.get_owners(table, record)

        try:
            record_id = record.id
        except:
            record_id = record
        # Session ownership?
        if not user_id:
            if not owner_user and record_id and \
               self.auth.s3_session_owns(table, record_id):
                # Session owns record
                return True
            else:
                return False

        # Individual record ownership
        if owner_user and owner_user == user_id:
            return True

        # OrgAuth?
        if self.policy == 6 and owner_org:
            # Must have the organisation's staff role
            if owner_org not in roles:
                return False
        elif self.policy == 7:
            # Must have both, the organisation's and the
            # facilities staff role
            if owner_org and owner_org not in roles:
                return False
            if owner_fac and owner_fac not in roles:
                return False

        # Owner?
        if not owner_role and not owner_user:
            # All authenticated users own this record
            return True
        elif owner_role and owner_role in roles:
            # user has owner role
            return True
        else:
            return False

    # -------------------------------------------------------------------------
    def hidden_modules(self):
        """
            List of modules to hide from the main menu
        """

        sr = self.auth.get_system_roles()

        hidden_modules = []
        if self.use_cacls:
            restricted_modules = [m for m in self.modules
                                    if self.modules[m].restricted]
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

        required = self.METHODS
        if p in required:
            permission = required[p]
        else:
            permission = self.READ

        if not c:
            c = self.controller
        if not f:
            f = self.function
        if t is None:
            tablename = "%s_%s" % (c, f)
        else:
            tablename = t

        # Hide disabled modules
        if self.modules and c not in self.modules:
            return False

        permitted = True
        if self.use_cacls:
            acl = self(c=c, f=f, table=tablename)
            if acl & permission != permission:
                permitted = False
        else:
            if permission != self.READ:
                permitted = self.auth.s3_logged_in()

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
    def page_restricted(self, c=None, f=None):
        """
            Checks whether a page is restricted (=whether ACLs
            are to be applied)

            @param c: controller
            @param f: function
        """

        page = "%s/%s" % (c, f)
        if page in self.unrestricted_pages:
            return False
        elif c not in self.modules or \
             c in self.modules and not self.modules[c].restricted:
            return False

        return True

    # -------------------------------------------------------------------------
    def applicable_acls(self, roles, racl, c=None, f=None, t=None):
        """
            Get the available ACLs for the particular situation

            @param roles: the roles of the current user
            @param racl: the required ACL
            @param c: controller
            @param f: function
            @param t: tablename

            @returns: None for no ACLs to apply (access granted), [] for
                      no ACLs matching the required permissions (access
                      denied), or a list of ACLs to apply.
        """

        db = current.db
        table = self.table

        if not self.use_cacls:
            # We do not use ACLs at all
            return None

        c = c or self.controller
        f = f or self.function
        if self.page_restricted(c=c, f=f):
            page_restricted = True
        else:
            page_restricted = False

        # Get page ACLs
        page_acls = None
        if page_restricted:
            # Base query
            query = (table.deleted != True) & \
                    (table.function == None)
            if f and self.use_facls:
                query = (query | (table.function == f))
            query &= (table.controller == c)
            # Do not use delegated ACLs except for policy 6 and 7
            if self.policy not in (6, 7):
                query &= ((table.organisation == None) & \
                          (table.facility == None))
            # Restrict to available roles
            if roles:
                query &= (table.group_id.belongs(roles))
            else:
                query &= (table.group_id == None)
            page_acls = db(query).select(table.ALL)
            if page_acls:
                if f and self.use_facls:
                    facl = [acl for acl in page_acls if acl.function != None]
                    if facl:
                        page_acls = facl
                page_acls = [acl for acl in page_acls
                                 if (acl.uacl & racl == racl or
                                     acl.oacl & racl == racl)]
            else:
                # Page is restricted, but no permitting ACL
                # available for this set of roles => no access
                return []

        # Get table ACLs
        table_acls = []
        if t and self.use_tacls:
            # Base query
            query = ((table.deleted != True) & \
                     (table.controller == None) & \
                     (table.function == None) &
                     (table.tablename == t))
            # Is the table restricted at all?
            restricted = db(query).select(limitby=(0, 1)).first() is not None
            # Do not use delegated ACLs except for policy 6 and 7
            if self.policy not in (6, 7):
                query &= ((table.organisation == None) & \
                          (table.facility == None))
            # Restrict to available roles
            if roles:
                query = (table.group_id.belongs(roles)) & query
            else:
                query = (table.group_id == None) & query
            table_acls = db(query).select(table.ALL)
            if restricted and table_acls:
                # if the table is restricted and there are ACLs
                # available for this set of roles, then deny access
                # if none of the ACLs gives the required permissions
                _debug("acls: %s" % table_acls)
                default = []
            else:
                # otherwise, if the table is unrestricted or there are
                # no restricting ACLs for this set of roles, then grant
                # access as per page_acls
                default = page_acls
            # Find matches
            table_acls = [acl for acl in table_acls
                              if (acl.uacl & racl == racl or
                                  acl.oacl & racl == racl)]
            if table_acls:
                # Found matching table ACLs, grant access
                return table_acls
            else:
                # No matching table ACLs found
                return default

        # default:
        return page_acls

    # -------------------------------------------------------------------------
    def accessible_query(self, table, *methods):
        """
            Query for records which the user is permitted to access
            with methods

            Example::
                query = auth.permission.accessible_query(table,
                                                         "read", "update")

                - requests a query for records that can be both read and
                  updated.

            @param table: the DB table
            @param methods: list of methods for which permission is
                            required (AND), any combination of "create",
                            "read", "update", "delete"
        """

        _debug("accessible_query(%s, %s)" % (table, methods))

        session = current.session
        policy = self.policy
        required = self.METHODS
        sr = self.auth.get_system_roles()

        OWNED_BY_ORG = "owned_by_organisation"
        OWNED_BY_FAC = "owned_by_facility"
        OWNED_BY_USER = "owned_by_user"
        OWNED_BY_ROLE = "owned_by_role"
        ALL_ORGS = "all_organisations"
        ALL_FACS = "all_facilities"

        # Default queries
        query = (table._id != None)
        no_access = (table._id == None)

        # Required ACL
        racl = reduce(lambda a, b: a | b,
                                   [required[m]
                                    for m in methods if m in required],
                                   self.NONE)
        if not racl:
            _debug("No permission specified, query=%s" % query)
            return query

        # User & Roles
        user_id = None
        if self.auth.user is not None:
            user_id = self.auth.user.id
        roles = []
        if session.s3 is not None:
            roles = session.s3.roles or []
        if sr.ADMIN in roles or sr.EDITOR in roles:
            _debug("Admin/Editor in Roles, query=%s" % query)
            return query

        # Org/Fac roles the user has
        org_roles = []
        fac_roles = []
        all_orgs = all_facs = False
        if policy in (6, 7):
            org_roles = list(roles)
        if policy == 7:
            fac_roles = list(roles)

        # Applicable ACLs
        acls = self.applicable_acls(roles, racl, t=table)
        permitted = False
        ownership_required = True

        if acls is None:
            permitted = True
            ownership_required = False

        elif acls:
            permitted = True
            for acl in acls:
                _debug("ACL: oacl=%04x uacl=%04x" % (acl.oacl, acl.uacl))
                if acl.uacl & racl == racl:
                    ownership_required = False
                    _debug("uACL found - no ownership required")
                if policy in (6, 7):
                    org_role = acl.organisation
                    if acl[ALL_ORGS]:
                        all_orgs = True
                    elif org_role and org_role not in org_roles:
                        org_roles.append(org_role)
                if policy == 7:
                    fac_role = acl.facility
                    if acl[ALL_FACS]:
                        all_facs = True
                    elif fac_role and fac_role not in fac_roles:
                        fac_roles.append(fac_role)

        if not permitted:
            _debug("No access")
            return no_access

        _debug("ownership_required=%s" % ownership_required)

        # Query fragments
        if OWNED_BY_ORG in table:
            has_org_role = ((table[OWNED_BY_ORG] == None) | \
                            (table[OWNED_BY_ORG].belongs(org_roles)))
        if OWNED_BY_FAC in table:
            has_fac_role = ((table[OWNED_BY_FAC] == None) | \
                            (table[OWNED_BY_FAC].belongs(fac_roles)))
        if OWNED_BY_USER in table:
            user_owns_record = (table[OWNED_BY_USER] == user_id)

        # OrgAuth
        q = None
        if policy == 6 and OWNED_BY_ORG in table and not all_orgs:
            q = has_org_role
            if user_id and OWNED_BY_USER in table:
                q |= user_owns_record
        elif policy == 7:
            if OWNED_BY_ORG in table and not all_orgs:
                q = has_org_role
            if OWNED_BY_FAC in table and not all_facs:
                if q is not None:
                    q &= has_fac_role
                else:
                    q = has_fac_role
            if q is not None and user_id and OWNED_BY_USER in table:
                q |= user_owns_record
        if q is not None:
            query = q

        if ownership_required:
            if not user_id:
                query = (table._id == None)
                if OWNED_BY_USER in table:
                    try:
                        records = session.owned_records.get(table._tablename,
                                                            None)
                    except:
                        pass
                    else:
                        if records:
                            query = (table._id.belongs(records))
            else:
                qowner = qrole = quser = None
                if OWNED_BY_ROLE in table:
                    qrole = (table.owned_by_role.belongs(roles))
                if OWNED_BY_USER in table and user_id:
                    quser = (table.owned_by_user == user_id)

                if qrole is not None:
                    qowner = qrole

                if quser is not None:
                    if qowner is not None:
                        qowner = (qowner | quser)
                    else:
                        qowner = quser
                if qowner is not None:
                    if query is not None:
                        query = query & qowner
                    else:
                        query = qowner

        # Fallback
        if query is None:
            query = (table._id > 0)
        _debug("Access granted, query=%s" % query)
        return query

    # -------------------------------------------------------------------------
    def ownership_required(self, table, *methods):
        """
            Check if record ownership is required for a method

            @param table: the table
            @param methods: methods to check (OR)

            @status: deprecated, using applicable_acls instead
        """

        sr = self.auth.get_system_roles()

        roles = []
        if current.session.s3 is not None:
            # No ownership required in policies without ACLs
            if not self.use_cacls:
                return False
            roles = current.session.s3.roles or []

        if sr.ADMIN in roles or sr.EDITOR in roles:
            return False # Admins and Editors do not need to own a record

        required = self.METHODS
        racl = reduce(lambda a, b: a | b,
                        [required[m] for m in methods if m in required],
                        self.NONE)
        if not racl:
            return False

        # Available ACLs
        pacl = self.page_acl()
        if not self.use_tacls:
            acl = pacl
        else:
            tacl = self.table_acl(table)
            acl = (tacl[0] & pacl[0], tacl[1] & pacl[1])

        # Ownership required?
        permitted = (acl[0] | acl[1]) & racl == racl
        ownership_required = False
        if not permitted:
            pkey = table.fields[0]
            query = (table[pkey] == None)
        elif "owned_by_role" in table or "owned_by_user" in table:
            ownership_required = permitted and acl[1] & racl != racl

        return ownership_required

    # -------------------------------------------------------------------------
    def has_permission(self, table, record=None, method=None):
        """
            Check permission to access a record

            @param table: the table
            @param record: the record or record ID (None for any record)
            @param method: the method (or tuple/list of methods),
                           any of "create", "read", "update", "delete"

            @note: when submitting a record, the record ID and the ownership
                   fields (="owned_by_user", "owned_by_role") must be contained
                   if available, otherwise the record will be re-loaded
        """

        _debug("has_permission(%s, %s, method=%s)" %
                   (table, record, method))

        required = self.METHODS

        if not isinstance(method, (list, tuple)):
            method = [method]

        # Required ACL
        racl = reduce(lambda a, b: a | b,
                     [required[m] for m in method if m in required], self.NONE)

        # Available ACL
        aacl = self(table=table, record=record)

        permitted = racl & aacl == racl
        _debug("permitted=%s" % permitted)
        return permitted

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
            site_types = self.auth.org_site_types
        else:
            if facility_type not in self.auth.org_site_types:
                return
            site_types = [s3db[facility_type]]
        for site_type in site_types:
            try:
                ftable = s3db[site_type]
                if not "site_id" in ftable.fields:
                    continue
                query = self.auth.s3_accessible_query("update", ftable)
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
        query = self.auth.s3_accessible_query("update", org_table)
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

    # -------------------------------------------------------------------------
    def fail(self):
        """
            Action upon insufficient permissions
        """

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

# =============================================================================

class S3Audit(object):

    """
        S3 Audit Trail Writer Class

        @author: Dominic König <dominic@aidiq.com>
    """

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
    """
        REST Method to manage ACLs (Role Manager UI for administrators)

        @todo: does not handle org-wise role assignment or
               delegation of permissions yet.
    """

    # Controllers to hide from the permissions matrix
    HIDE_CONTROLLER = ("admin", "default")

    # Roles to hide from the permissions matrix
    # @todo: deprecate
    HIDE_ROLES = (1, 4)

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
        """
            View/Update roles of a user
        """

        output = dict()

        db = current.db
        T = current.T

        CANCEL = T("Cancel")

        session = current.session
        manager = current.manager
        sr = session.s3.system_roles
        request = self.request
        crud_settings = manager.s3.crud
        formstyle = crud_settings.formstyle

        auth = manager.auth
        gtable = auth.settings.table_group
        mtable = auth.settings.table_membership

        if r.interactive:
            if r.record:
                user = r.record
                user_id = user.id
                username = user.email
                query = (mtable.deleted != True) &\
                        (mtable.user_id == user_id)
                memberships = db(query).select()
                memberships = Storage([(str(m.group_id), m.id)
                                       for m in memberships])
                roles = db(gtable.deleted != True).select(gtable.ALL)
                roles = Storage([(str(g.id), " %s" % g.role)
                                 for g in roles
                                 if g.hidden != True and \
                                    g.id not in (sr.ANONYMOUS,
                                                 sr.AUTHENTICATED)])
                field = Storage(name="roles",
                                requires = IS_IN_SET(roles, multiple=True))
                widget = CheckboxesWidgetS3.widget(field, memberships.keys())

                if session.s3.cancel:
                    cancel = session.s3.cancel
                else:
                    cancel = r.url(method="")
                form = FORM(TABLE(
                            TR(TD(widget)),
                            TR(TD(INPUT(_type="submit", _value=T("Save")),
                                  A(CANCEL,
                                    _href=cancel, _class="action-lnk")))))

                if form.accepts(request.post_vars, session):
                    assign = form.vars.roles
                    for role in roles:
                        query = (mtable.deleted != True) & \
                                (mtable.user_id == user_id) & \
                                (mtable.group_id == role)
                        _set = db(query)
                        if str(role) not in assign:
                            _set.update(deleted=True)
                        else:
                            membership = _set.select(limitby=(0, 1)).first()
                            if not membership:
                                mtable.insert(user_id=user_id, group_id=role)
                    session.confirmation = T("User Updated")
                    redirect(r.url(method=""))

                output.update(title="%s - %s" %
                                    (T("Assigned Roles"), username),
                              form=form)

                current.response.view = "admin/user_roles.html"

            else:
                session.error = T("No user to update")
                redirect(r.url(method=""))
        else:
            r.error(501, manager.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def _users(self, r, **attr):
        """
            View/Update users of a role
        """

        output = dict()

        session = current.session
        manager = current.manager
        request = self.request

        db = current.db
        T = current.T
        auth = manager.auth

        utable = auth.settings.table_user
        gtable = auth.settings.table_group
        mtable = auth.settings.table_membership

        if r.interactive:
            if r.record:

                role_id = r.record.id
                role_name = r.record.role
                role_desc = r.record.description

                title = "%s: %s" % (T("Role"), role_name)
                output.update(title=title,
                              description=role_desc,
                              group=role_id)

                if auth.settings.username:
                    username = "username"
                else:
                    username = "email"

                # @todo: Audit
                users = db().select(utable.ALL)
                query = (mtable.deleted != True) & \
                        (mtable.group_id == role_id)
                assigned = db(query).select(mtable.ALL)

                assigned_users = [row.user_id for row in assigned]
                unassigned_users = [(row.id, row)
                                    for row in users
                                    if row.id not in assigned_users]

                # Delete form
                if assigned_users:
                    thead = THEAD(TR(TH(),
                                     TH(T("Name")),
                                     TH(T("Username")),
                                     TH(T("Remove?"))))
                    trows = []
                    i = 0
                    for user in users:
                        if user.id not in assigned_users:
                            continue
                        _class = i % 2 and "even" or "odd"
                        i += 1
                        trow = TR(TD(A(), _name="Id"),
                                  TD("%s %s" % (user.first_name,
                                                user.last_name)),
                                  TD(user[username]),
                                  TD(INPUT(_type="checkbox",
                                           _name="d_%s" % user.id,
                                           _class="remove_item")),
                                _class=_class)
                        trows.append(trow)
                    trows.append(TR(TD(), TD(), TD(),
                                TD(INPUT(_id="submit_delete_button",
                                         _type="submit",
                                         _value=T("Remove")))))
                    tbody = TBODY(trows)
                    del_form = TABLE(thead, tbody, _id="list",
                                     _class="dataTable display")
                else:
                    del_form = T("No users with this role")

                del_form = FORM(DIV(del_form, _id="table-container"),
                                    _name="del_form")

                # Add form
                uname = lambda u: \
                        "%s: %s %s" % (u.id, u.first_name, u.last_name)
                u_opts = [OPTION(uname(u[1]),
                          _value=u[0]) for u in unassigned_users]
                if u_opts:
                    u_opts = [OPTION("",
                              _value=None, _selected="selected")] + u_opts
                    u_select = DIV(TABLE(TR(
                                    TD(SELECT(_name="new_user", *u_opts)),
                                    TD(INPUT(_type="submit",
                                             _id="submit_add_button",
                                             _value=T("Add"))))))
                else:
                    u_select = T("No further users can be added")
                add_form = FORM(DIV(u_select), _name="add_form")

                # Process delete form
                if del_form.accepts(request.post_vars,
                                    session, formname="del_form"):
                    del_ids = [v[2:] for v in del_form.vars
                                     if v[:2] == "d_" and
                                        del_form.vars[v] == "on"]
                    query = (mtable.deleted != True) & \
                            (mtable.group_id == role_id) & \
                            (mtable.user_id.belongs(del_ids))
                    db(query).update(deleted=True)
                    redirect(r.url())

                # Process add form
                if add_form.accepts(request.post_vars,
                                    session, formname="add_form"):
                    if add_form.vars.new_user:
                        mtable.insert(group_id=role_id,
                                      user_id=add_form.vars.new_user)
                    redirect(r.url())

                form = DIV(H4(T("Users with this role")), del_form,
                           H4(T("Add new users")), add_form)
                list_btn = A(T("Back to Roles List"),
                             _href=URL(c="admin", f="role"),
                             _class="action-btn")
                edit_btn = A(T("Edit Role"),
                             _href=URL(c="admin", f="role",
                                       args=[role_id]),
                             _class="action-btn")
                output.update(form=form, list_btn=list_btn, edit_btn=edit_btn)

                current.response.view = "admin/role_users.html"

            else:
                session.error = T("No role to update")
                redirect(r.there())
        else:
            r.error(501, manager.BAD_FORMAT)

        return output

# =============================================================================

