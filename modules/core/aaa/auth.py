"""
    Authentication and Authorization

    Copyright: (c) 2010-2022 Sahana Software Foundation

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
           )

import binascii
import json
import time

from uuid import uuid4

from gluon import current, redirect, CRYPT, DAL, SQLFORM, URL, \
                  A, DIV, INPUT, LABEL, SPAN, XML, \
                  IS_EMAIL, IS_EMPTY_OR, IS_EXPR, IS_IN_DB, IS_IN_SET, \
                  IS_LOWER, IS_NOT_EMPTY, IS_NOT_IN_DB

from gluon.storage import Storage
from gluon.tools import Auth, callback, DEFAULT, replace_id
from gluon.utils import web2py_uuid

from s3dal import Row, Rows, Query, Field, original_tablename, filter_fields

from ..controller import CRUDRequest
from ..model import MetaFields, CommentsField
from ..tools import IS_ISO639_2_LANGUAGE_CODE, S3Represent, S3Tracker, \
                    s3_addrow, s3_mark_required, s3_str

from .lock import AccountLockingMixin
from .permissions import S3Permission
from .consent import ConsentTracking

# =============================================================================
class AuthS3(AccountLockingMixin, Auth):
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
            - verify_unlock
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
            - s3_password

        - S3 custom authentication methods:
            - s3_impersonate
            - s3_logged_in

        - S3 user role management:
            - get_system_roles
            - s3_set_roles
            - s3_create_role
            - s3_delete_role
            - s3_assign_role
            - s3_remove_role
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

        - S3 overrides of web2py authorization methods:
            - has_membership (with deleted flag support)
            - requires_membership

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

        # Deployment options
        deployment_settings = current.deployment_settings
        log_failed_logins = deployment_settings.get_auth_log_failed_logins()

        # Adjust settings
        settings = self.settings
        settings.lock_keys = False

        settings.login_userfield = "email"
        if log_failed_logins is True: # rather than "VALIDONLY"
            settings.log_all_failed_logins = True

        settings.lock_keys = True

        # Adjust messages
        messages = self.messages
        messages.lock_keys = False

        # @ToDo Move these to deployment_settings
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
        #messages.label_time_stamp = "Timestamp"
        #messages.label_client_ip = "Client IP"
        #messages.label_origin = "Origin"
        #messages.label_description = "Description"
        messages.label_acting_user = "Acting User"

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
        messages.verify_email = "Click on the link %(url)s to verify your email.\n\nYou activation code is: %(code)s"
        messages.verify_email_subject = "%(system_name)s - Verify Email"
        messages.welcome_email_subject = "Welcome to %(system_name)s"
        messages.welcome_email = \
"""Welcome to %(system_name)s
 - You can start using %(system_name)s at: %(url)s
 - To edit your profile go to: %(url)s%(profile)s
Thank you"""
        messages.locked_email_subject = "%(system_name)s - Account Locked"
        messages.locked_email = \
"""Your account on %(system_name)s has been locked due to excessive failed login attempts.
 - Please change your password at your earliest convenience.
 Thank you"""
        messages.unlocked_email_subject = "%(system_name)s - Account Unlocked"
        messages.unlocked_email = \
"""Your account on %(system_name)s has been unlocked.
 - You can now log in again.
 Thank you"""
        messages.unlock_email_subject = "%(system_name)s - Unlock Account"
        messages.unlock_email = \
"""Your account on %(system_name)s has been locked due to excessive failed login attempts.

To unlock your account, open this link:
%(url)s

Your unlock code is: %(code)s"""
        messages.user_unlocked_log = "User %%(%s)s unlocked via email verification" % settings.login_userfield

        # Log messages
        messages.user_disabled_log = "User %(user_id)s disabled"
        messages.user_enabled_log = "User %(user_id)s (re-)enabled"
        messages.user_approved_log = "User %(user_id)s approved"
        messages.user_locked_log = "User %%(%s)s locked due to excessive failed login attempts" % settings.login_userfield
        messages.login_attempts_exceeded = "Login attempts exceeded"

        # Optional log messages
        if log_failed_logins:
            messages.login_failed_log = "Login for user %%(%s)s failed" % settings.login_userfield

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
        self.org_site_types = Storage(transport_airport = T("Airport"),
                                      msg_basestation = T("Cell Tower"),
                                      cr_shelter = T("Shelter"),
                                      org_facility = T("Facility"), # @ToDo: Use deployment setting for label
                                      org_office = T("Office"),
                                      transport_heliport = T("Heliport"),
                                      hms_hospital = T("Hospital"),
                                      fire_station = T("Fire Station"),
                                      dvi_morgue = T("Morgue"),
                                      transport_seaport = T("Seaport"),
                                      inv_warehouse = T("Warehouse"),
                                      )

        # Name prefixes of tables which must not be manipulated from remote,
        # CLI can override with auth.override=True
        self.PROTECTED = ("admin",)

        self._user_represent = None

    # -------------------------------------------------------------------------
    def define_tables(self, migrate=True, fake_migrate=False):
        """
            Define auth tables, to be called unless tables are defined
            manually

            Examples:
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
                Field("locked", "boolean",
                      default=False,
                      readable=False, writable=False),
                Field("failed_attempts", "integer",
                      default=0,
                      readable=False, writable=False),
                Field("locked_until", "datetime",
                      default=None,
                      readable=False, writable=False),
                Field("deleted", "boolean",
                      default=False,
                      readable=False, writable=False),
                Field("timestmp", "datetime",
                      default="",
                      readable=False, writable=False),
                CommentsField(readable=False, writable=False),
                # Additional meta fields required for sync:
                MetaFields.uuid(),
                #MetaFields.mci(),
                MetaFields.created_on(),
                MetaFields.modified_on(),
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
                      label = messages.label_role,
                      ),
                Field("description", "text",
                      label = messages.label_description,
                      ),
                # Additional meta fields required for sync:
                MetaFields.created_on(),
                MetaFields.modified_on(),
                MetaFields.deleted(),
                #MetaFields.deleted_fk(),
                #MetaFields.deleted_rb(),
                migrate = migrate,
                fake_migrate = fake_migrate,
                )
            gtable = settings.table_group = db[gname]

        # Group membership table (user<->role)
        if not settings.table_membership:
            define_table(
                settings.table_membership_name,
                Field("user_id", utable,
                      requires = IS_IN_DB(db, "%s.id" % uname,
                                          "%(id)s: %(first_name)s %(last_name)s"),
                      label = messages.label_user_id,
                      ),
                Field("group_id", gtable,
                      requires = IS_IN_DB(db, "%s.id" % gname,
                                          "%(id)s: %(role)s"),
                      represent = S3Represent(lookup=gname, fields=["role"]),
                      label = messages.label_group_id,
                      ),
                # Realm
                Field("pe_id", "integer"),
                Field("system", "boolean",
                      default = False,
                      ),
                migrate = migrate,
                fake_migrate = fake_migrate,
                *MetaFields.sync_meta_fields())
            settings.table_membership = db[settings.table_membership_name]

        # Define Eden permission table
        self.permission.define_table(migrate = migrate,
                                     fake_migrate = fake_migrate,
                                     )

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
        if not settings.table_event:
            request = current.request
            define_table(
                settings.table_event_name,
                Field("time_stamp", "datetime",
                      default = request.utcnow,
                      label = messages.label_time_stamp
                      ),
                Field("client_ip",
                      default = request.client,
                      label = messages.label_client_ip
                      ),
                Field("user_id", utable,
                      default = None,
                      requires = IS_IN_DB(db, "%s.id" % uname,
                                          "%(id)s: %(first_name)s %(last_name)s"),
                      label = messages.label_acting_user
                      ),
                Field("origin", length=512,
                      default = "auth",
                      label = messages.label_origin,
                      requires = IS_NOT_EMPTY(),
                      ),
                Field("description", "text",
                      default = "",
                      label = messages.label_description,
                      requires = IS_NOT_EMPTY(),
                      ),
                migrate = migrate,
                fake_migrate = fake_migrate,
                *MetaFields.sync_meta_fields())
            settings.table_event = db[settings.table_event_name]

    # -------------------------------------------------------------------------
    def ignore_min_password_length(self):
        """
            Disable min_length validation for password, e.g. during login
        """

        settings = self.settings

        utable = settings.table_user

        requires = utable[settings.password_field].requires
        if requires:
            if isinstance(requires, (list, tuple)):
                requires = requires[-1]
            try:
                requires.min_length = 0
            except:
                pass

    # -------------------------------------------------------------------------
    def login_bare(self, username, password):
        """
            Logs user in
                - extended to understand session.s3.roles
                - extended to handle login failures
        """

        self.ignore_min_password_length()

        settings = self.settings

        utable = settings.table_user
        userfield = settings.login_userfield
        passfield = settings.password_field

        query = (utable[userfield] == username)
        user = current.db(query).select(limitby=(0, 1)).first()

        if user and not user.registration_key:
            password = utable[passfield].validate(password)[0]
            if user[passfield] == password:
                user = Storage(filter_fields(utable, user, allow_id=True))
                current.session.auth = Storage(user = user,
                                               last_visit = current.request.now,
                                               expiration = settings.expiration,
                                               )
                self.unlock_user(user)
                self.user = user
                self.s3_set_roles()
                return user
            else:
                self.handle_failed_login(user=user)

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
              lost_pw_link = None,
              register_link = True,
              formstyle = None,
              inline = False, # Set to True to use an 'inline' variant of the style
              ):
        """
            Overrides Web2Py's login() to use custom flash styles & utcnow

            Returns:
                a login form
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

        # Username (email) is required for login, convert to lowercase
        userfield = settings.login_userfield
        old_requires = utable[userfield].requires
        utable[userfield].requires = [IS_NOT_EMPTY(), IS_LOWER()]

        # Disable min_length for password during login
        passfield = settings.password_field
        self.ignore_min_password_length()

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

            if not formstyle:
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
                                  _href = URL(f=controller, args="register"),
                                  _id = "register-btn",
                                  _class = "action-lnk",
                                  )
                buttons.append(register_link)

            # Lost-password action link
            if deployment_settings.get_auth_password_retrieval():
                if lost_pw_link is None:
                    lost_pw_link = deployment_settings.get_auth_password_changes()
                if lost_pw_link:
                    lost_pw_link = A(T("Lost Password"),
                                     _href = URL(f="user", args="retrieve_password"),
                                     _class = "action-lnk",
                                     )
                    buttons.append(lost_pw_link)

            # Add submit button
            #if buttons:
            submit_button = INPUT(_type="submit", _value=T("Login"))
            buttons.insert(0, submit_button)

            form = SQLFORM(utable,
                           fields = [userfield, passfield],
                           hidden = {"_next": request.vars._next},
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
                          DIV(INPUT(_type = "checkbox",
                                    _class = "checkbox",
                                    _id = "auth_user_remember",
                                    _name = "remember",
                                    ),
                              LABEL(messages.label_remember_me,
                                    _for = "auth_user_remember",
                                    ),
                              ),
                          "",
                          formstyle,
                          "auth_user_remember__row",
                          )

            if deployment_settings.get_auth_set_presence_on_login():
                s3_addrow(form,
                          "",
                          INPUT(_id = "auth_user_clientlocation",
                                _name = "auth_user_clientlocation",
                                _style = "display:none",
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
                existing = None
                query = (utable[userfield] == form.vars[userfield])
                user = db(query).select(limitby=(0, 1)).first()

                if user:
                    # User in db
                    existing = temp_user = user

                    # Check if login is permitted
                    if self.is_user_locked(temp_user):
                        # Account is locked due to too many failed login attempts
                        self.handle_failed_login(user=temp_user)
                        response.error = messages.login_attempts_exceeded
                        response.error_code = 423
                        return form

                    from .lock import LOCKED
                    registration_key = temp_user.registration_key
                    if registration_key == "pending":
                        # Account is verified, but pending approval
                        response.warning = deployment_settings.get_auth_registration_pending()
                        return form
                    elif registration_key in ("disabled", "blocked"):
                        # Account has been disabled|blocked by ADMIN
                        response.error = messages.login_disabled
                        return form
                    elif registration_key is not None and \
                         registration_key != LOCKED and \
                         registration_key.strip():
                        # Account has not yet been verified
                        response.warning = messages.registration_verifying
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
                    # Invalid login
                    if existing or settings.log_all_failed_logins:
                        self.log_event(messages.login_failed_log, request.post_vars)
                    session.error = messages.invalid_login

                    # Handle failed login attempts
                    if existing:
                        self.handle_failed_login(user=existing)

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
                user = self.get_or_create_user(filter_fields(utable, cas_user))
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
            user = Storage(filter_fields(utable, user, allow_id=True))
            self.login_user(user)
        if log and self.user:
            self.log_event(log, self.user)

        # How to continue
        if next is DEFAULT:
            if accepted_form:
                # Check for pending consent upon login?
                pending_consent = deployment_settings.get_auth_consent_check()
                if callable(pending_consent):
                    pending_consent = pending_consent()
                if pending_consent:
                    next = URL(c="default", f="user", args=["consent"])

                # Check for mandatory page after login
                mandatory = deployment_settings.get_auth_mandatory_page()
                if mandatory:
                    next_url = mandatory() if callable(mandatory) else mandatory
                else:
                    next_url = None
                if next_url:
                    next = next_url

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
        else:
            redirect(next)

        return form

    # -------------------------------------------------------------------------
    def change_password(self,
                        next = DEFAULT,
                        onvalidation = DEFAULT,
                        onaccept = DEFAULT,
                        log = DEFAULT,
                        ):
        """
            Returns a form that lets the user change password
        """

        if not self.is_logged_in():
            redirect(self.settings.login_url,
                     client_side = self.settings.client_side)

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
                  label = messages.old_password,
                  # No minimum length for old password
                  #requires = utable[passfield].requires,
                  requires = CRYPT(key = settings.hmac_key,
                                   digest_alg = "sha512",
                                   ),
                  ),
            Field("new_password", "password",
                  label = messages.new_password,
                  requires = utable[passfield].requires,
                  ),
            Field("new_password2", "password",
                  label = messages.verify_password,
                  requires = [IS_EXPR("value==%s" % repr(request.vars.new_password),
                                      messages.mismatched_password,
                                      ),
                              ],
                  ),
            submit_button = messages.password_change_button,
            hidden = {"_next": next},
            formstyle = current.deployment_settings.get_ui_formstyle(),
            separator = settings.label_separator
        )
        form.add_class("auth_change_password")

        if form.accepts(request, session,
                        formname = "change_password",
                        onvalidation = onvalidation,
                        hideerror = settings.hideerror):

            if not form.vars["old_password"] == s.select(limitby = (0, 1),
                                                         orderby_on_limitby = False
                                                         ).first()[passfield]:
                form.errors["old_password"] = messages.invalid_password
            else:
                d = {passfield: str(form.vars.new_password)}
                s.update(**d)
                session.confirmation = messages.password_changed
                self.log_event(log, self.user)
                callback(onaccept, form)
                if not next:
                    next = self.url(args = request.args)
                else:
                    next = replace_id(next, form)
                redirect(next, client_side=settings.client_side)

        return form

    # -------------------------------------------------------------------------
    def reset_password(self,
                       next = DEFAULT,
                       onvalidation = DEFAULT,
                       onaccept = DEFAULT,
                       log = DEFAULT,
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
                  requires = IS_EXPR("value==%s" % repr(request.vars.new_password),
                                     messages.mismatched_password,
                                     ),
                  ),
            submit_button = messages.password_change_button,
            hidden = {"_next": next},
            formstyle = current.deployment_settings.get_ui_formstyle(),
            separator = settings.label_separator
            )
        if form.accepts(request, session,
                        onvalidation = onvalidation,
                        hideerror = settings.hideerror):
            user.update_record(
                **{passfield: str(form.vars.new_password),
                   "registration_key": "",
                   "reset_password_key": "",
                   })
            session.flash = messages.password_changed
            if settings.login_after_password_change:
                user = Storage(filter_fields(table_user, user, allow_id=True))
                self.login_user(user)
            callback(onaccept, form)
            redirect(next, client_side=settings.client_side)
        return form

    # -------------------------------------------------------------------------
    def request_reset_password(self,
                               next = DEFAULT,
                               onvalidation = DEFAULT,
                               onaccept = DEFAULT,
                               log = DEFAULT,
                               ):
        """
            Returns a form to reset the user password, overrides web2py's
            version of the method to apply Eden formstyles.

            Args:
                next: URL to redirect to after successful form submission
                onvalidation: callback to validate password reset form
                onaccept: callback to post-process password reset request
                log: event description for the log (string)
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
                       hidden = {"_next": next},
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
            user = user,
            last_visit = request.now,
            expiration = req_vars.get("remember", False) and \
                settings.long_expiration or settings.expiration,
            remember = "remember" in req_vars,
            hmac_key = web2py_uuid()
            )

        self.user = user
        self.s3_set_roles()

        # Set a Cookie to present user with login box by default
        self.set_cookie()

        # If the user had been locked, unlock them now
        self.unlock_user(user)

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
                                                  timestmp = request.utcnow)
            elif closestpoint != 0:
                s3tracker(db.pr_person,
                          person_id).set_location(closestpoint,
                                                  timestmp = request.utcnow)

    # -------------------------------------------------------------------------
    def consent(self):
        """
            Consent question form, e.g.
                - when consent requires renewal, or
                - new consent questions need to be asked, or
                - user has been added by ADMIN and shall give consent upon login
                - ...

            Note:
                This form cannot meaningfully prevent the user from simply
                bypassing the question and navigating away. To prevent the
                user from accessing functionality for which consent is
                mandatory, the respective controllers must check for consent
                using ConsentTracking.has_consented, and refuse if not given
                (though they can still redirect to this form where useful).
        """

        T = current.T

        request = current.request
        response = current.response
        session = current.session
        settings = current.deployment_settings

        next_url = request.get_vars.get("_next")
        if not next_url:
            next_url = settings.get_auth_login_next()
            if callable(next_url):
                next_url = next_url()
        if not next_url:
            next_url = URL(c = "default", f = "index")

        session.s3.pending_consent = False

        # Requires login
        if not self.s3_logged_in():
            session.error = T("Authentication required")
            redirect(URL(c = "default", f = "user",
                         args = ["login"],
                         vars = {"_next": URL(args=current.request.args)},
                         ))

        # Requires person record
        person_id = self.s3_logged_in_person()
        if not person_id:
            session.error = T("No person record for the current user")
            redirect(next_url)

        # Get all pending consent questions for the current user
        pending_consent = settings.get_auth_consent_check()
        if callable(pending_consent):
            pending_consent = pending_consent()
        if not pending_consent:
            session.warning = T("No pending consent questions for the current user")
            redirect(next_url)
        else:
            response.warning = T("Consent required")
            session.s3.pending_consent = True

        # Instantiate Consent Tracker
        consent = ConsentTracking(processing_types=pending_consent)

        # Form fields
        formfields = [Field("consent",
                            label = T("Consent"),
                            widget = consent.widget,
                            ),
                      ]
        # Generate labels (and mark required fields in the process)
        labels, has_required = s3_mark_required(formfields)
        response.s3.has_required = has_required

        # Form buttons
        SUBMIT = T("Submit")
        buttons = [INPUT(_type = "submit",
                         _value = SUBMIT,
                         ),
                   ]

        # Construct the form
        response.form_label_separator = ""
        form = SQLFORM.factory(table_name = "auth_consent",
                               record = None,
                               hidden = {"_next": request.vars._next},
                               labels = labels,
                               separator = "",
                               showid = False,
                               submit_button = SUBMIT,
                               delete_label = self.messages.delete_label,
                               formstyle = settings.get_ui_formstyle(),
                               buttons = buttons,
                               *formfields)

        # Identify form for CSS
        form.add_class("auth_consent")

        if form.accepts(current.request.vars,
                        current.session,
                        formname = "consent",
                        ):

            consent.track(person_id, form.vars.get("consent"))
            session.s3.pending_consent = False
            session.confirmation = T("Consent registered")
            redirect(next_url)

        # Remind the user that form should be submitted even if they didn't
        # enter anything:
        response.s3.jquery_ready.append('''S3SetNavigateAwayConfirm();
$('form.auth_consent').submit(S3ClearNavigateAwayConfirm);''')

        return form

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

            Returns:
                a registration form
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
            redirect(URL(args = ["login"]))

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
        buttons = [INPUT(_type = "submit",
                         _value = REGISTER,
                         ),
                   A(T("Login"),
                     _href = URL(f="user", args="login"),
                     _id = "login-btn",
                     _class = "action-lnk",
                     ),
                   ]
        current.response.form_label_separator = ""
        form = SQLFORM(utable,
                       hidden = {"_next": request.vars._next},
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
            item = row.element("input",
                               _name = passfield,
                               )
            if item:
                field_id = "%s_password_two" % utablename
                s3_addrow(form,
                          LABEL(DIV("%s:" % messages.verify_password,
                                    SPAN("*",
                                         _class = "req",
                                         ),
                                    _for = "password_two",
                                    _id = field_id + SQLFORM.ID_LABEL_SUFFIX,
                                    ),
                                ),
                          INPUT(_name = "password_two",
                                _id = field_id,
                                _type = "password",
                                requires = IS_EXPR("value==%s" % \
                                    repr(request.vars.get(passfield, None)),
                                error_message = messages.mismatched_password)
                                ),
                          "",
                          formstyle,
                          field_id + SQLFORM.ID_ROW_SUFFIX,
                          position = i + 1,
                          )

        # S3: Insert Home phone field into form
        if deployment_settings.get_auth_registration_requests_home_phone():
            for i, row in enumerate(form[0].components):
                item = row.element("input", _name="email")
                if item:
                    field_id = "%s_home" % utablename
                    s3_addrow(form,
                              LABEL("%s:" % T("Home Phone"),
                                    _for = "home",
                                    _id = field_id + SQLFORM.ID_LABEL_SUFFIX,
                                    ),
                              INPUT(_name = "home",
                                    _id = field_id,
                                    ),
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
                                    _for = "mobile",
                                    _id = field_id + SQLFORM.ID_LABEL_SUFFIX,
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
            comment = DIV(_class = "stickytip",
                          _title = "%s|%s" % (label,
                                              self.messages.help_image % \
                                                {"gravatar": A("Gravatar",
                                                               _target = "top",
                                                               _href = "http://gravatar.com",
                                                               )
                                                 }))
            field_id = "%s_image" % utablename
            widget = SQLFORM.widgets["upload"].widget(current.s3db.pr_image.image, None)
            s3_addrow(form,
                      LABEL("%s:" % label,
                            _for = "image",
                            _id = field_id + SQLFORM.ID_LABEL_SUFFIX,
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
                {"terms_of_service": A(T("Terms of Service"),
                                       _href = URL(c="default", f="tos"),
                                       _target = "_blank",
                                       )}
            label = XML("%s:" % label)
            s3_addrow(form,
                      LABEL(label,
                            _for = "tos",
                            _id = field_id + SQLFORM.ID_LABEL_SUFFIX,
                            ),
                      INPUT(_name = "tos",
                            _id = field_id,
                            _type = "checkbox",
                            ),
                      "",
                      formstyle,
                      field_id + SQLFORM.ID_ROW_SUFFIX,
                      )

        if settings.captcha != None:
            form[0].insert(-1, DIV("", settings.captcha, ""))

        # Set default registration key, so new users are prevented
        # from logging in until approved
        key = str(uuid4())
        code = uuid4().hex[-6:].upper()
        utable.registration_key.default = self.keyhash(key, code)

        if form.accepts(request.vars, session, formname="register",
                        onvalidation=onvalidation):

            # Save temporary user fields
            self.s3_user_register_onaccept(form)

            users = db(utable.id > 0).select(utable.id,
                                             limitby = (0, 2))
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
                user = Storage(filter_fields(utable, form.vars, allow_id=True))
                self.login_user(user)

                self.s3_send_welcome_email(form.vars)

            elif settings.registration_requires_verification:
                # Request User Verify their Email
                # System Details for Verification Email
                verify_url = URL(c = "default",
                                 f = "user",
                                 args = ["verify_email", key],
                                 scheme = "https" if request.is_https else "http",
                                 )
                system = {"system_name": deployment_settings.get_system_name(),
                          "url": verify_url,
                          "code": code,
                          }

                # Try to send the Verification Email
                if not settings.mailer or \
                   not settings.mailer.settings.server or \
                   not settings.mailer.send(to = form.vars.email,
                                            subject = messages.verify_email_subject % system,
                                            message = messages.verify_email % system,
                                            ):
                    current.response.error = messages.email_verification_failed
                    return form

                # @ToDo: Deployment Setting?
                #session.confirmation = messages.email_sent
                next = URL(c="default", f="message",
                           args = ["verify_email_sent"],
                           vars = {"email": form.vars.email},
                           )
            else:
                # Does the user need to be approved?
                approved = self.s3_verify_user(form.vars)

                if approved:
                    # Log them in
                    if "language" not in form.vars:
                        # Was missing from login form
                        form.vars.language = T.accepted_language
                    user = Storage(filter_fields(utable, form.vars, allow_id=True))
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

            Args:
                user: the auth_user record (Row)
        """

        mailer = self.settings.mailer
        if not mailer or not mailer.settings.server:
            return False

        reset_password_key = str(int(time.time())) + '-' + web2py_uuid()
        reset_password_url = "%s/default/user/reset_password?key=%s" % \
                             (current.response.s3.base_url, reset_password_key)

        message = self.messages.reset_password % {"url": reset_password_url}
        if mailer.send(to = user.email,
                       subject = self.messages.reset_password_subject,
                       message = message):
            user.update_record(reset_password_key = reset_password_key)
            return True

        return False

    # -------------------------------------------------------------------------
    def add_membership(self,
                       group_id = None,
                       user_id = None,
                       role = None,
                       entity = None,
                       ):
        """
            Gives user_id membership of group_id or role
                - extended to support Entities

            Args:
                group_id: the auth_group ID
                user_id: the auth_user ID (defaults to logged-in user)
                role: role name (alternative to group_id)
                entity: the person entity to assign the membership for

            Returns:
                the membership record ID
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
    def verify_email(self, next=DEFAULT, log=DEFAULT):
        """
            Dialog to verify the email address of a user; presents
            a form to enter the activation code that has been sent
            with the verification email

            Args:
                next: the URL to redirect to after processing
                log: the log message for the event

            Returns:
                FORM
        """

        T = current.T

        request = current.request
        response = current.response
        session = current.session

        settings = current.deployment_settings

        # Customise the resource
        customise = settings.customise_resource("auth_user")
        if customise:
            customise(request, "auth_user")

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

            auth_settings = self.settings

            # Get registration key from URL
            code = form.vars.activation_code

            # Find the pending user account
            utable = auth_settings.table_user
            query = (utable.registration_key == self.keyhash(key, code))
            user = current.db(query).select(limitby=(0, 1)).first()
            if not user:
                session.error = T("Registration not found")
                redirect(auth_settings.verify_email_next)

            if log == DEFAULT:
                log = self.messages.verify_email_log
            if next == DEFAULT:
                next = auth_settings.verify_email_next

            approved = self.s3_verify_user(user)
            if approved:
                # Log them in
                user = Storage(filter_fields(utable, user, allow_id=True))
                self.login_user(user)
            if log:
                self.log_event(log, user)

            redirect(next)

        return form

    # -------------------------------------------------------------------------
    def verify_unlock(self, next=DEFAULT, log=DEFAULT):
        """
            Form to unlock a locked account using the code sent by email
        """

        T = current.T

        request = current.request
        response = current.response
        session = current.session

        settings = current.deployment_settings

        from .lock import LOCKED

        if request.env.request_method == "POST":
            key = request.post_vars.registration_key
        elif len(request.args) > 1:
            key = request.args[-1]
        else:
            key = None
        if not key:
            session.error = T("Missing unlock key")
            redirect(URL(c="default", f="index"))

        formfields = [Field("activation_code",
                            label = T("Please enter your Unlock Code"),
                            requires = IS_NOT_EMPTY(),
                            ),
                      ]

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
                               *formfields)

        if form.accepts(request.vars,
                        session,
                        formname = "unlock_confirm",
                        ):

            auth_settings = self.settings
            code = form.vars.activation_code

            utable = auth_settings.table_user
            query = (utable.reset_password_key == self.keyhash(key, code)) & \
                    (utable.registration_key == LOCKED)
            user = current.db(query).select(limitby=(0, 1)).first()
            if not user:
                session.error = T("Unlock verification failed")
                redirect(settings.get_auth_verify_unlock_next())

            if log == DEFAULT:
                log = self.messages.user_unlocked_log
            if next == DEFAULT:
                next = settings.get_auth_verify_unlock_next()

            self.unlock_user(user, log=log, notify=True)
            user.update_record(reset_password_key = "")

            session.confirmation = T("Your account has been unlocked. You can now log in.")
            redirect(next)

        response.title = T("Unlock Account")
        return form

    # -------------------------------------------------------------------------
    @staticmethod
    def keyhash(key, code):
        """
            Generate a hash of the activation code using
            the registration key

            Args:
                key: the registration key
                code: the activation code

            Returns:
                the hash as string
        """

        crypt = CRYPT(key=key, digest_alg="sha512", salt=None)
        return str(crypt(code.upper())[0])

    # -------------------------------------------------------------------------
    def profile(self,
                next = DEFAULT,
                onvalidation = DEFAULT,
                onaccept = DEFAULT,
                log = DEFAULT,
                ):
        """
            Returns a form that lets the user change his/her profile
                - patched for S3 to use s3_mark_required
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

        formstyle = deployment_settings.get_ui_formstyle()
        current.response.form_label_separator = ""
        form = SQLFORM(utable,
                       self.user.id,
                       fields = settings.profile_fields,
                       labels = labels,
                       hidden = {"_next": next},
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
            self.user.update(filter_fields(utable, form.vars))
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

        return form

    # -------------------------------------------------------------------------
    @property
    def user_represent(self):
        """
            Common auth_UserRepresent instance for meta-fields (lazy property)

            Returns:
                S3Represent instance
        """

        represent = self._user_represent
        if represent is None:

            if current.deployment_settings.get_ui_auth_user_represent() == "name":
                show_name = True
                show_email = False
            else:
                show_name = False
                show_email = True

            represent = current.s3db.auth_UserRepresent(show_name = show_name,
                                                        show_email = show_email,
                                                        show_link = False,
                                                        )
            self._user_represent = represent

        return represent

    # -------------------------------------------------------------------------
    def configure_user_fields(self, pe_ids=None):
        """
            Configure User Fields - for registration & user administration

            Args:
                pe_ids: an optional list of pe_ids for the Org Filter
                        i.e. org_admin coming from admin.py/user()
        """

        T = current.T
        db = current.db
        s3db = current.s3db
        request = current.request
        messages = self.messages
        cmessages = current.messages
        settings = self.settings
        deployment_settings = current.deployment_settings

        from ..tools import IS_ONE_OF
        from ..ui import S3MultiSelectWidget

        # Should we use multi-select widgets rather than simple dropdowns?
        multiselect_widget = bool(deployment_settings.get_ui_multiselect_widget())

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
            language.comment = DIV(_class = "tooltip",
                                   _title = "%s|%s" % (T("Language"),
                                                       T("The language you wish the site to be displayed in.")
                                                       ),
                                   )
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
                from core.ui.layouts import PopupLink
                org_crud_strings = s3db.crud_strings["org_organisation"]
                organisation_id.comment = PopupLink(c = "org",
                                                    f = "organisation",
                                                    label = org_crud_strings.label_create,
                                                    title = org_crud_strings.title_list,
                                                    )
                #from ..ui import S3OrganisationAutocompleteWidget
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
            #from core.ui.layouts import PopupLink
            #ogroup_crud_strings = s3db.crud_strings["org_group"]
            #org_group_id.comment = PopupLink(c = "org",
            #                                 f = "group",
            #                                 label = ogroup_crud_strings.label_create,
            #                                 title = ogroup_crud_strings.title_list,
            #                                 )
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
                    from ..tools import IS_ONE_OF_EMPTY
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
                                         orderby = "org_site.name",
                                         sort = True)
                #from ..ui import S3SiteAutocompleteWidget
                #field.widget = S3SiteAutocompleteWidget()
                field.comment = DIV(_class = "tooltip",
                                    _title = "%s|%s" % (T("Facility"),
                                                        T("Select the default site.")
                                                        ))
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
                link_user_to.comment = DIV(_class = "tooltip",
                                           _title = "%s|%s" % (link_user_to.label,
                                                               T("Will create and link your user account to the following records")
                                                               ))

    # -------------------------------------------------------------------------
    def s3_import_prep(self, tree):
        """
            Looks up Pseudo-reference Integer fields from Names, e.g.:
            auth_membership.pe_id from org_organisation.name=<Org Name>
                - called when users are imported from CSV

            Args:
                tree: the element tree of the import
        """

        db = current.db
        s3db = current.s3db
        set_record_owner = self.s3_set_record_owner
        update_super = s3db.update_super
        otable = s3db.org_organisation
        btable = s3db.org_organisation_branch

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
                    (otable.deleted == False)
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
                        (ltable.deleted == False)
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
                    (ptable.deleted == False) & \
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
        js_append('''$.extend($.validator.messages, { required: "%s" });''' % T("This field is required."))

        script = '''\n'''.join(js_global)
        s3.js_global.append(script)

        # Call script after Global config done
        s3.jquery_ready.append('''s3_register_validation()''')

    # -------------------------------------------------------------------------
    def s3_auth_user_register_onaccept(self, email, user_id):
        """
            Allows customisation of the process for creating/updating users
                - called by s3_approve_user when new users are created
                  or approved

            Args:
                email: the user's email address
                user_id: the auth_user ID
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
            Sets session.auth.user for authorstamp, etc, and approves user
            (to set registration groups, such as AUTHENTICATED, link to Person)

            Designed to be called when a user is created through:
                - registration via OAuth, LDAP, etc
        """

        user = form.vars
        current.session.auth = Storage(user=user)
        self.s3_approve_user(user)

    # -------------------------------------------------------------------------
    @staticmethod
    def s3_user_register_onaccept(form):
        """
            Stores the user's email & profile image in auth_user_temp,
            to be added to their person record when created on approval

            Designed to be called when a user is created through:
                - registration
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
    @staticmethod
    def s3_approve_user_message(user, languages):
        """
            Default construction of Messages to (Org_)Admins to approve a new user
        """

        approve_user_message = \
"""Your action is required to approve a New User for %(system_name)s:
%(first_name)s %(last_name)s
%(email)s
Please go to %(url)s to approve this user."""

        T = current.T
        subjects = {}
        messages = {}
        first_name = user.first_name
        last_name = user.last_name
        email = user.email
        user_id = user.id
        base_url = current.response.s3.base_url
        system_name = current.deployment_settings.get_system_name()
        for language in languages:
            T.force(language)
            subjects[language] = \
                s3_str(T("%(system_name)s - New User Registration Approval Pending") % \
                        {"system_name": system_name})
            messages[language] = s3_str(T(approve_user_message) % \
                        {"system_name": system_name,
                         "first_name": first_name,
                         "last_name": last_name,
                         "email": email,
                         "url": "%(base_url)s/admin/user/%(id)s" % \
                                {"base_url": base_url,
                                 "id": user_id,
                                 },
                         })

        # Restore language for UI
        T.force(current.session.s3.language)

        return subjects, messages

    # -------------------------------------------------------------------------
    def s3_verify_user(self, user):
        """"
            Sends a message to the approver to notify them if a user needs
            approval

            Designed to be called when a user is verified through:
                - responding to their verification email
                - if verification isn't required

            Returns:
                boolean - if the user has been approved

            Notes:
                - If deployment_settings.auth.always_notify_approver = True,
                  send them notification regardless
                - If approval isn't required - calls s3_approve_user
        """

        db = current.db
        deployment_settings = current.deployment_settings
        session = current.session
        auth_messages = self.messages
        utable = self.settings.table_user

        # Lookup the Approver
        approver, organisation_id = self.s3_approver(user)

        if deployment_settings.get_auth_registration_requires_approval() and approver:
            approved = False
            db(utable.id == user.id).update(registration_key = "pending")

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
                db(utable.id == user.id).update(organisation_id = organisation_id)
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
                                                         limitby = (0, 1)
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

        if message == "approve_user":
            # Customised Message construction?
            approve_user_message = deployment_settings.get_auth_approve_user_message()
            if callable(approve_user_message):
                subjects, messages = approve_user_message(user, languages)
            else:
                # Default Message construction
                subjects, messages = self.s3_approve_user_message(user, languages)
        elif message == "new_user":
            # @ToDo: Allow custom Message construction
            T = current.T
            subjects = {}
            messages = {}
            first_name = user.first_name
            last_name = user.last_name
            email = user.email
            system_name = deployment_settings.get_system_name()
            for language in languages:
                T.force(language)
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

        if not result:
            # Don't prevent registration just because email not configured
            #db.rollback()
            current.response.error = auth_messages.email_send_failed
            return False

        return approved

    # -------------------------------------------------------------------------
    def s3_approve_user(self, user, password=None, defaults=False):
        """
            Adds user to the 'Authenticated' role, and any default roles

            Designed to be called when a user is created through:
                - prepop
                - approved automatically during registration
                - approved by admin
                - added by admin
                - updated by admin

            Args:
                user: the user Storage() or Row
                password: optional password to include in a custom welcome_email
        """

        user_id = user.id
        if not user_id:
            return

        db = current.db
        s3db = current.s3db

        deployment_settings = current.deployment_settings
        settings = self.settings

        sr = self.get_system_roles()

        # Add to AUTHENTICATED role
        add_membership = self.add_membership
        add_membership(sr.AUTHENTICATED, user_id)

        # Reload the user record if any details are missing
        utable = settings.table_user
        fields = ("id", "email", "organisation_id", "org_group_id", "site_id", "link_user_to")
        if any(fn not in user for fn in fields):
            user = db(utable.id == user_id).select(*fields, limitby=(0, 1)).first()
        if not user:
            return

        organisation_id = user.organisation_id
        link_user_to = user.link_user_to or utable.link_user_to.default or []

        # Add User to required registration roles
        entity_roles = deployment_settings.get_auth_registration_roles()
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
            # If this is the 1st user to register for an organisation, give
            # them the OrgAdmin role for that organisation
            entity = s3db.pr_get_pe_id("org_organisation", organisation_id)

            # We only need to check whether there is an OrgAdmin yet, because
            # if there were any other user for this organisation, they would
            # necessarily be OrgAdmin due to this rule
            mtable = settings.table_membership
            query = (mtable.group_id == sr.ORG_ADMIN) & \
                    (mtable.pe_id == entity)
            if not db(query).select(mtable.id, limitby=(0, 1)).first():
                # No OrgAdmin yet
                add_membership(sr.ORG_ADMIN, user_id, entity=entity)

        # Link user to person, staff and other records as required
        self.s3_link_user(user)

        # Track consent
        if deployment_settings.get_auth_consent_tracking():
            ConsentTracking.register_consent(user_id)

        # Run any custom on-approval routines
        self.s3_auth_user_register_onaccept(user.email, user_id)

        if current.response.s3.bulk is True:
            # Non-interactive imports should stop here
            return

        # Allow them to login (enable the account)
        db(utable.id == user_id).update(registration_key="")

        # Approve User's Organisation (if they created a new one during registration)
        if organisation_id and \
           "org_organisation" in deployment_settings.get_auth_record_approval_required_for():
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
            Links the user account to various tables:
                - Creates (if not existing) User's Organisation and links User
                - Creates (if not existing) User's Person Record and links User
                - Creates (if not existing) User's Human Resource Record and links User
                - Calls s3_link_to_member

            Designed to be called when a user is created & approved through:
                - prepop
                - approved automatically during registration
                - approved by admin
                - added by admin
                - updated by admin

            Args:
                user: the user account (auth_user record)
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

            Args:
                user: the user record
                organisation_id: the user's organisation_id
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
                else:
                    other = None

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
                                                  modified_by = user.id,
                                                  **owner)
                    else:
                        person_id = ptable.insert(first_name = first_name,
                                                  last_name = last_name,
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
                        s3db.onaccept(ptable, person, method="create")

                        # Insert a link
                        ltable.insert(user_id=user.id, pe_id=pe_id)

                        # Add the email to pr_contact
                        ctable.insert(pe_id = pe_id,
                                      contact_method = "EMAIL",
                                      priority = 1,
                                      value = email,
                                      **owner)

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

            Args:
                user: the user account record
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

            Args:
                user: the user account record
                person_id: the person record ID associated with this user
        """

        db = current.db
        s3db = current.s3db

        org_group_id = user.get("org_group_id")
        if not org_group_id or not person_id:
            return None

        # Default status to "Member"
        stable = s3db.org_group_person_status
        query = (stable.name.lower() == "member") & \
                (stable.deleted == False)
        row = db(query).select(stable.id, limitby=(0, 1)).first()
        if row:
            status_id = row.id
        else:
            status_id = None

        # Check if link exists
        ltable = s3db.org_group_person
        query = (ltable.person_id == person_id) & \
                (ltable.org_group_id == org_group_id) & \
                (ltable.deleted == False)
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
            Link the user to a human resource record and make them owner

            Args:
                user: the user record
                person_id: the person ID linked to that user
                hr_type: the human resource type (staff/volunteer)
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
                request = CRUDRequest("hrm", "human_resource",
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
                if isinstance(person_id, list):
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

            Args:
                user: the user record
                person_id: the person ID linked to that user
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
                    request = CRUDRequest("member", "membership",
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

            Args:
                user - the user record (form.vars when done direct)
            Returns:
                approver, organisation_id

            Note:
                If approver = False, user is automatically approved by whitelist.

            TODO Support multiple approvers per Org - via Org Admin (or specific Role?)
                 Split into separate functions to returning approver & finding users' org
                 from auth_organisations
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
                - suitable e.g. for users from Facebook/Google who don't
                  verify their emails

            Args:
                user: the user dict, must contain "email", and can
                      contain "language" for translation of the message
                password: optional password to include in a custom welcome_email
        """

        settings = current.deployment_settings
        if not settings.get_auth_registration_welcome_email():
            # Welcome-email disabled
            return

        messages = self.messages
        if not settings.get_mail_sender():
            # Email sender not configured, mail system disabled
            current.response.warning = messages.unable_send_email
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

        recipient = user.get("email")
        if recipient:
            if settings.has_module("msg"):
                send_email = current.msg.send_email
            else:
                send_email = current.mail.send
            result = send_email(recipient,
                                subject = subject,
                                message = message,
                                )
        else:
            result = False

        if not result:
            current.response.warning = messages.unable_send_email

    # -------------------------------------------------------------------------
    def s3_password(self, length=32):
        """
            Generate a random password
        """

        if length == 32:
            password = uuid4().hex
        else:
            import random
            import string
            password = "".join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(length))

        crypted = CRYPT(key = self.settings.hmac_key,
                        #min_length = current.deploymentsettings.get_auth_password_min_length(),
                        digest_alg = "sha512",
                        )(password)[0]

        return password, crypted

    # -------------------------------------------------------------------------
    def s3_anonymise_password(self, record_id, field, value):
        """
            Anonymise the password

            Args:
                record_id: the auth_user record ID
                field: the password Field
                value: the password hash

            Returns:
                the new random password hash
        """

        return self.s3_password()[1]

    # -------------------------------------------------------------------------
    def s3_anonymise_roles(self, record_id, field, value):
        """
            Remove all roles

            Args:
                record_id: the auth_user record ID
                field: the id Field
                value: the id

            Returns:
                the record_id
        """

        roles = self.s3_get_roles(record_id)
        if roles:
            self.s3_remove_role(record_id, roles)
        return record_id

    # -------------------------------------------------------------------------
    # S3-specific authentication methods
    # -------------------------------------------------------------------------
    def s3_impersonate(self, user_id):
        """
            S3 framework function
                - designed to be used within tasks, which are run in a separate
                  request & hence don't have access to current.auth

            Args:
                user_id: auth.user.id or auth.user.email
        """

        settings = self.settings
        utable = settings.table_user
        query = None
        if not user_id:
            # Anonymous
            user = None
        elif isinstance(user_id, str) and not user_id.isdigit():
            query = (utable[settings.login_userfield] == user_id)
        else:
            query = (utable.id == user_id)

        if query is not None:
            user = current.db(query).select(limitby=(0, 1)).first()
            if not user:
                # Invalid user ID
                raise ValueError("User not found")
            user = Storage(filter_fields(utable, user, allow_id=True))

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

            Returns:
                None if master key authentication is disabled or wasn't
                attempted, otherwise True|False whether it succeeded
        """

        success = None

        s3 = current.response.s3
        if s3.masterkey_auth_failed:
            # Already failed during this request cycle, no point trying again
            success = False
        else:
            from .masterkey import S3MasterKey
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
            try:
                basic = self.basic()
            except binascii.Error:
                # Credentials present but encoded incorrectly
                return False

            return basic[2] # accepted True|False

        return True

    # -------------------------------------------------------------------------
    # Role Management
    # -------------------------------------------------------------------------
    def get_role_id(self, uid):
        """
            Get the role ID for a role UID

            Args:
                uid: the role UID
            Returns:
                the corresponding auth_group record ID
        """

        gtable = self.settings.table_group
        query = (gtable.uuid == uid) & (gtable.deleted == False)

        row = current.db(query).select(gtable.id,
                                       cache = (current.cache.ram, 600),
                                       limitby=(0, 1),
                                       ).first()

        return row.id if row else None

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
            query = (gtable.deleted == False) & \
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
            Get the pe_ids of all managed organisations, e.g. for filters

            Returns:
                - True if unrestricted (i.e. site-wide role)
                - list of pe_ids if restricted
                - None if user does not manage any orgs

            Note:
                The result only means that the user has a *_ADMIN role
                for those organisations, but that does not imply any
                particular permissions =>
                use auth.permission.permitted_realms for access control
        """

        user = self.user
        if not user:
            return None

        has_role = self.s3_has_role
        sr = self.get_system_roles()

        if has_role(sr.ADMIN):
            return True

        elif self.s3_has_roles((sr.ORG_ADMIN, sr.ORG_GROUP_ADMIN)):
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
                pe_ids = set()
                for role in (sr.ORG_ADMIN, sr.ORG_GROUP_ADMIN):
                    if role not in self.user.realms:
                        continue
                    realm = self.user.realms[role]
                    if realm is None:
                        return True
                    pe_ids.update(realm)
                pe_ids = list(pe_ids) if pe_ids else None
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
        AUTHENTICATED = system_roles.AUTHENTICATED

        session_roles = {ANONYMOUS} if ANONYMOUS else set()

        if self.user:

            db = current.db
            s3db = current.s3db

            user_id = self.user.id

            # Logout disabled/blocked users immediately
            utable = self.settings.table_user
            query = (utable.id == user_id) & \
                    (utable.registration_key.belongs(("disabled", "blocked")))
            if db(query).select(utable.id, limitby=(0, 1)).first():
                session.renew(clear_session=True)
                redirect(URL(c="default", f="index"))

            # Set pe_id for current user
            ltable = s3db.table("pr_person_user")
            if ltable is not None:
                row = db(ltable.user_id == user_id).select(ltable.pe_id,
                                                           limitby = (0, 1),
                                                           cache = s3db.cache,
                                                           ).first()
                self.user["pe_id"] = row.pe_id if row else None
            else:
                self.user["pe_id"] = None

            # Get all current auth_memberships of the user
            mtable = self.settings.table_membership
            query = (mtable.deleted == False) & \
                    (mtable.user_id == user_id) & \
                    (mtable.group_id != None)
            rows = db(query).select(mtable.group_id,
                                    mtable.pe_id,
                                    cacheable = True,
                                    )

            # Add all group_ids to session.s3.roles
            session_roles |= {row.group_id for row in rows}
            if AUTHENTICATED:
                session_roles.add(AUTHENTICATED)

            # Realms:
            # Permissions of a group apply only for records owned by any of
            # the entities which belong to the realm of the group membership

            # These realms apply for every authenticated user:

            if not permission.entity_realm:
                # All roles apply site-wide (i.e. no realms, policy 5 and below)
                realms = {row.group_id: None for row in rows}
            else:
                # Roles are limited to realms (policy 6 and above)
                default_realm = s3db.pr_default_realms(self.user["pe_id"])

                # Store the realms:
                realms = {}
                for row in rows:

                    group_id = row.group_id
                    if group_id == system_roles.ADMIN:
                        # Admin is not realm-restrictable
                        realm = realms[group_id] = None
                    elif group_id in realms:
                        realm = realms[group_id]
                    else:
                        realm = realms[group_id] = []
                    if realm is None:
                        continue

                    pe_id = row.pe_id
                    if pe_id is None:
                        if default_realm:
                            realm.extend([e for e in default_realm if e not in realm])
                        if not realm:
                            del realms[group_id]
                    elif pe_id == 0:
                        realms[group_id] = None
                    elif pe_id not in realm:
                        realm.append(pe_id)

                if permission.entity_hierarchy:
                    # Realms include subsidiaries of the realm entities

                    # Get all entities in realms
                    entities = []
                    append = entities.append
                    for realm in realms.values():
                        if realm is not None:
                            for entity in realm:
                                if entity not in entities:
                                    append(entity)

                    # Lookup the subsidiaries of all realms and extensions
                    descendants = s3db.pr_descendants(entities)

                    # Add the subsidiaries to the realms
                    for group_id, realm in realms.items():
                        if realm is None:
                            continue
                        append = realm.append
                        for entity in list(realm):
                            if entity in descendants:
                                for subsidiary in descendants[entity]:
                                    if subsidiary not in realm:
                                        append(subsidiary)

            # These realms apply for every authenticated user:
            for role in (ANONYMOUS, AUTHENTICATED):
                if role:
                    realms[role] = None
            self.user["realms"] = Storage(realms)

        session.s3.roles = list(session_roles)

    # -------------------------------------------------------------------------
    def s3_create_role(self, role, description=None, *acls, **args):
        """
            Back-end method to create roles with ACLs

            Args:
               role: display name for the role
               description: description of the role (optional)
               acls: list of initial ACLs to assign to this role

            Kwargs:
               name: a unique name for the role
               hidden: hide this role completely from the RoleManager
               system: role can be assigned, but neither modified nor
                       deleted in the RoleManager
               protected: role can be assigned and edited, but not
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

            Args:
                role_id: the ID or UID of the role

            Note:
                Protected roles cannot be deleted with this function,
                need to reset the protected-flag first to override.
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
                                limitby = (0, 1),
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
    def s3_assign_role(self, user_id, group_id, for_pe=None, system=False):
        """
            Assigns a role to a user (add the user to a user group)

            Args:
                user_id: the record ID of the user account
                group_id: the record ID(s)/UID(s) of the group
                for_pe: the person entity (pe_id) to restrict the group
                        membership to, possible values:
                           - None: use default realm (entities the user is
                             affiliated with)
                           - 0: site-wide realm (no entity-restriction)
                           - X: restrict to records owned by entity X
                system: set the system-flag for any new role assignments

            Notes:
                - strings are assumed to be group UIDs
                - for_pe will be ignored for ADMIN, ANONYMOUS and AUTHENTICATED
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
            query = (gtable.deleted == False) & query
            groups = db(query).select(gtable.id, gtable.uuid)
            group_ids = [g.id for g in groups]
            missing = [uuid for uuid in uuids
                       if uuid not in [g.uuid for g in groups]]
            for m in missing:
                group_id = self.s3_create_role(m, uid=m)
                if group_id:
                    group_ids.append(group_id)

        # Find the assigned groups
        query = (mtable.deleted == False) & \
                (mtable.user_id == user_id) & \
                (mtable.group_id.belongs(group_ids) & \
                (mtable.pe_id == for_pe))
        assigned = db(query).select(mtable.group_id)
        assigned_groups = [g.group_id for g in assigned]

        # Add missing memberships
        sr = self.get_system_roles()
        unrestrictable = [str(sr.ADMIN),
                          str(sr.ANONYMOUS),
                          str(sr.AUTHENTICATED),
                          ]
        for gid in group_ids:
            if gid not in assigned_groups:
                membership = {"user_id": user_id,
                              "group_id": gid,
                              "system": system,
                              }
                if for_pe is not None and str(gid) not in unrestrictable:
                    membership["pe_id"] = for_pe
                mtable.insert(**membership)

        # Update roles for current user if required
        if self.user and str(user_id) == str(self.user.id):
            self.s3_set_roles()

    # -------------------------------------------------------------------------
    def s3_remove_role(self, user_id, group_id, for_pe=DEFAULT):
        """
            Removes a role assignment from a user account

            Args:
                user_id: the record ID of the user account
                group_id: the record ID(s)/UID(s) of the role
                for_pe: only remove the group membership for this
                        realm, possible values:
                           - None: only remove for the default realm
                           - 0: only remove for the site-wide realm
                           - X: only remove for entity X
                           - []: remove for any realms (=default)

            Note:
                strings are assumed to be role UIDs
        """

        if not group_id:
            return

        db = current.db
        gtable = self.settings.table_group
        mtable = self.settings.table_membership

        # Find the group IDs
        query = group_ids = None
        if isinstance(group_id, (list, tuple)):
            if isinstance(group_id[0], str):
                query = (gtable.uuid.belongs(group_id))
            else:
                group_ids = group_id
        else:
            if isinstance(group_id, str):
                query = (gtable.uuid == group_id)
            else:
                group_ids = {group_id}
        if query is not None:
            group_ids = db(query & (gtable.deleted == False))._select(gtable.id)

        # Get the assigned groups
        query = (mtable.deleted == False) & \
                (mtable.user_id == user_id) & \
                (mtable.group_id.belongs(group_ids))

        sr = self.get_system_roles()
        unrestrictable = [str(sr.ADMIN),
                          str(sr.ANONYMOUS),
                          str(sr.AUTHENTICATED)]
        if for_pe is not DEFAULT and for_pe != []:
            query &= ((mtable.pe_id == for_pe) | \
                      (mtable.group_id.belongs(unrestrictable)))
        memberships = db(query).select(mtable.id,
                                       mtable.user_id,
                                       mtable.group_id,
                                       mtable.pe_id,
                                       )

        # Archive the memberships
        for m in memberships:
            deleted_fk = {"user_id": m.user_id, "group_id": m.group_id}
            if m.pe_id:
                deleted_fk["pe_id"] = m.pe_id
            m.update_record(deleted = True,
                            deleted_fk = json.dumps(deleted_fk),
                            user_id = None,
                            group_id = None,
                            pe_id = None,
                            )

        # Update roles for current user if required
        if self.user and str(user_id) == str(self.user.id):
            self.s3_set_roles()

    # -------------------------------------------------------------------------
    def s3_get_roles(self, user_id, for_pe=DEFAULT):
        """
            Lookup all roles which have been assigned to user for an entity

            Args:
                user_id: the user_id
                for_pe: the entity (pe_id) or list of entities
        """

        if not user_id:
            return []

        mtable = self.settings.table_membership
        query = (mtable.deleted == False) & \
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

            Args:
                role: the record ID or UID of the role
                for_pe: check for this particular realm, possible values:
                           - None: for any entity
                           - 0: site-wide
                           - X: for entity X
                include_admin: ADMIN matches all Roles
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
                role = self.get_role_id(role)
                if not role:
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

            Args:
                roles: list|tuple|set of role IDs or UIDs
                for_pe: check for this particular realm, possible values:
                               None - for any entity
                               0 - site-wide
                               X - for entity X
                all: check whether the user has all of the roles
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
            if isinstance(role, str):
                resolve.add(role)
            else:
                check.add(role)

        if resolve:
            gtable = self.settings.table_group
            query = (gtable.uuid.belongs(resolve)) & \
                    (gtable.deleted == False)
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

            Args:
                group_id: the group record ID
                for_pe: show only group members for this PE

            Returns:
                a list of the user_ids for members of a group
        """

        mtable = self.settings.table_membership

        query = (mtable.deleted == False) & \
                (mtable.group_id == group_id)
        if for_pe is None:
            query &= (mtable.pe_id == None)
        elif for_pe is not DEFAULT:
            query &= (mtable.pe_id == for_pe)
        members = current.db(query).select(mtable.user_id)
        return [m.user_id for m in members]

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

            Args:
                person_id: the pr_person record ID, or a user email address
                pe_id: the person entity ID, alternatively
        """

        result = None

        if isinstance(person_id, str) and not person_id.isdigit():
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

            Args:
                user_id: the user ID
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

            Args:
                user_id: list of user IDs
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
                                               limitby = (0, 1),
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
                                               cache = s3db.cache,
                                               limitby = (0, 1),
                                               orderby = ~htable.modified_on,
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

            Args:
                method: the access method as string, one of
                        "create", "read", "update", "delete"
                table: the table or tablename
                record_id: the record ID (if any)
                c: the controller name (overrides current.request)
                f: the function name (overrides current.request)
        """

        if self.override:
            return True

        if not hasattr(table, "_tablename"):
            tablename = table
            table = current.s3db.table(tablename, db_only=True)
            if table is None:
                current.log.warning("Permission check on Table %s failed as couldn't load table. Module disabled?" % tablename)
                # Return a different Falsy value
                return None

        policy = current.deployment_settings.get_security_policy()

        if isinstance(method, (list, tuple)) and policy not in (3, 4, 5, 6, 7):
            return all(self.s3_has_permission(m, table, record_id=record_id, c=c, f=f) for m in method)

        sr = self.get_system_roles()
        permission = self.permission

        # Simple policy
        if policy == 1:
            required = permission.METHODS.get(method) or 0
            if required == permission.READ:
                # All users can read, including anonymous users
                authorised = True
            else:
                # Authentication required for all other methods
                authorised = self.s3_logged_in()

        # Editor policy
        elif policy == 2:
            required = permission.METHODS.get(method) or 0
            if required == permission.READ:
                # All users can read, including anonymous users
                authorised = True
            elif required == permission.CREATE or \
                 record_id == 0 and required == permission.UPDATE:
                # Authenticated users can create records, and update
                # certain default records (e.g. their profile)
                authorised = self.s3_logged_in()
            else:
                # Otherwise, must be EDITOR or record owner
                authorised = self.s3_has_role(sr.EDITOR)
                if not authorised and self.user and "owned_by_user" in table:
                    query = (table.id == record_id)
                    record = current.db(query).select(table.owned_by_user,
                                                      limitby = (0, 1),
                                                      ).first()
                    if record and self.user.id == record.owned_by_user:
                        authorised = True

        # Use S3Permission
        elif policy in (3, 4, 5, 6, 7):
            authorised = permission.has_permission(method,
                                                   c = c,
                                                   f = f,
                                                   t = table,
                                                   record = record_id,
                                                   )

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

            Args:
                method: the access method as string, one of:
                        "create", "read", "update" or "delete"
                table: the table or table name
                c: the controller name (overrides current.request)
                f: the function name (overrides current.request)

            NB This method does not work on GAE because it uses JOIN and IN
        """

        if not hasattr(table, "_tablename"):
            table = current.s3db[table]

        if self.override:
            return table.id > 0

        sr = self.get_system_roles()

        policy = current.deployment_settings.get_security_policy()

        if policy == 1:
            # "simple" security policy: show all records
            return table.id > 0
        elif policy == 2:
            # "editor" security policy: show all records
            return table.id > 0
        elif policy in (3, 4, 5, 6, 7):
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
    def has_membership(self, group_id=None, user_id=None, role=None):
        """
            Checks if user is member of group_id or role

            Extends Web2Py's has_membership() to add:
                - Respect for the deleted flag in auth_membership
                - Custom Flash style

            Args:
                group_id: the group ID to check membership for
                user_id: the user ID to check (defaults to current user)
                role: the role name (alternative to group_id)

            Returns:
                True if the user is a member of the group, False otherwise
        """

        # Allow override
        if self.override:
            return True

        # Determine user_id
        if not user_id and self.user:
            user_id = self.user.id
        elif user_id:
            # Validate the user_id: invalid user_id must not pass has_membership test
            utable = self.table_user()
            if not self.db(utable.id==user_id).select(utable.id, limitby=(0, 1)).first():
                return False

        # Resolve group_id from role if needed
        # TODO support group UIDs (e.g. "ADMIN" instead of 1)
        group_id = group_id or self.id_group(role)
        try:
            group_id = int(group_id)
        except:
            group_id = self.id_group(group_id)  # interpret group_id as a role

        ret = False

        sr = self.get_system_roles()
        if group_id == sr.ANONYMOUS:
            # All users are members of the ANONYMOUS group
            ret = True
        elif group_id == sr.AUTHENTICATED and user_id:
            # All registered users are members of the AUTHENTICATED group
            ret = True
        elif group_id and user_id:
            membership = self.table_membership()
            query = (membership.user_id == user_id) & \
                    (membership.group_id == group_id) & \
                    (membership.deleted == False)
            if self.db(query).select(membership.id, limitby=(0, 1)).first():
                ret = True

        # Log the check
        log = self.messages.has_membership_log
        if log:
            self.log_event(log, {"user_id": user_id,
                                 "group_id": group_id,
                                 "check": ret,
                                 })
        return ret

    # -------------------------------------------------------------------------
    def requires_membership(self, role):
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

    # -------------------------------------------------------------------------
    # Record Ownership
    # -------------------------------------------------------------------------
    def s3_make_session_owner(self, table, record_id):
        """
            Makes the current session owner of a record

            Args:
                table: the table or table name
                record_id: the record ID
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

            Args:
                table: the table or table name
                record_id: the record ID
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

            Args:
                table: the table or table name (default: all tables)
                record_id: the record ID (default: all records)
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

            Args:
                table: the table
                record: the record or record ID
                update: True to update realm_entity in all realm-components
                fields: dict of {ownership_field:value}
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

        data = {k: v for k, v in fields.items() if k in ownership_fields}
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
                            force_update = False,
                            **fields):
        """
            Set the record owned_by_user, owned_by_group and realm_entity
            for a record (auto-detect values).
                - to be called by CRUD and Importer during record creation.

            Args:
                table: the Table (or table name)
                record: the record (or record ID)
                force_update: True to update all fields regardless of
                              the current value in the record, False
                              to only update if current value is None
                fields: override auto-detected values, see keywords

            Keyword Args:
                owned_by_user: the auth_user ID of the owner user
                owned_by_group: the auth_group ID of the owner group
                realm_entity: the pe_id of the realm entity, or a tuple
                              (instance_type, instance_id) to lookup the
                              pe_id, e.g. ("org_organisation", 2)

            Notes:
                - only use with force_update for deliberate owner changes (i.e.
                  with explicit owned_by_user/owned_by_group) - autodetected
                  values can have undesirable side-effects. For mere realm
                  updates use set_realm_entity instead.
                - if used with force_update, this will also update the
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
            row = current.db(query).select(*fields_to_load, limitby=(0, 1)).first()
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
                  "pr_person_availability",
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
                entity = fields.get(REALM, 0)
                realm_entity = self.get_realm_entity(table, row, entity=entity)
                data[REALM] = realm_entity

        self.s3_update_record_owner(table, row, update=force_update, **data)

    # -------------------------------------------------------------------------
    def set_realm_entity(self, table, records, entity=0, force_update=False):
        """
            Update the realm entity for records, will also update the
            realm in all configured realm-entities
                - to be called by CRUD and Importer during record update.

            Args:
                table: the Table (or tablename)
                records: the records to set the realm entity for
                            - a single record
                            - a single record ID
                            - a list of records, or a Rows object
                            - a list of record IDs
                            - a query to find records in table
                entity: the realm entity
                            - an person entity ID
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

            Args:
                table: the Table
                record: the record (as Row or dict)
                entity: the entity (pe_id)
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

            Args:
                table: the table
                record: a record, record ID or a query
                data: the field/value pairs to update
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
               not any(f in supertable.fields for f in data):
                continue
            tables[super_key(supertable)] = supertable

        if not isinstance(record, (Row, dict)) or \
           any(f not in record for f in tables):
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
            instance_records = db(query).select(limitby=limitby, *fields)
        else:
            instance_records = [record]
        if not instance_records:
            return

        for instance_record in instance_records:
            for skey, supertable in tables.items():
                if skey in instance_record:
                    query = (supertable[skey] == instance_record[skey])
                else:
                    continue
                updates = {f: v for f, v in data.items() if f in supertable.fields}
                if not updates:
                    continue
                db(query).update(**updates)

    # -------------------------------------------------------------------------
    def permitted_facilities(self,
                             table = None,
                             error_msg = None,
                             redirect_on_error = True,
                             facility_type = None
                             ):
        """
            If there are no facilities that the user has permission for,
            prevents create & update of records in table & gives a
            warning if the user tries to.

            Args:
                table: the table or table name
                error_msg: error message
                redirect_on_error: whether to redirect on error
                facility_type: restrict to this particular type of
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
                    query &= (ftable.deleted == False)
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
                                table = None,
                                error_msg = None,
                                redirect_on_error = True
                                ):
        """
            If there are no organisations that the user has update
            permission for, prevents create & update of a record in
            table & gives an warning if the user tries to.

            Args:
                table: the table or table name
                error_msg: error message
                redirect_on_error: whether to redirect on error
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

# END =========================================================================
