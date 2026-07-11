"""
    Locking of user accounts

    Copyright: (c) 2025 Sahana Software Foundation

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

import datetime
import time

from gluon import current, URL
from uuid import uuid4

LOCKED = "failed"

# Additional failed attempts after the preliminary threshold before hard lock
HARD_LOCK_EXTRA_ATTEMPTS = 5

# =============================================================================
class AccountLockingMixin:
    """ Auth mixin to handle locking of accounts """

    def is_user_hard_locked(self, user):
        """
            Checks whether a user account is hard-locked (ADMIN unlock only)

            Args:
                user: the auth_user Row

            Returns:
                boolean
        """

        if not user or user.registration_key != LOCKED:
            return False

        return not user.locked_until or user.locked_until > current.request.utcnow

    # -------------------------------------------------------------------------
    def is_user_preliminarily_locked(self, user):
        """
            Checks whether a user account is preliminarily locked
            (self-service email unlock may still be available)

            Args:
                user: the auth_user Row

            Returns:
                boolean
        """

        return user and user.locked and not self.is_user_hard_locked(user)

    # -------------------------------------------------------------------------
    def is_user_locked(self, user):
        """
            Checks whether a user account is locked (preliminary or hard)

            Args:
                user: the auth_user Row

            Returns:
                boolean
        """

        return self.is_user_hard_locked(user) or self.is_user_preliminarily_locked(user)

    # -------------------------------------------------------------------------
    def can_send_unlock_email(self, user):
        """
            Whether self-service email unlock is available for this user

            Args:
                user: the auth_user Row

            Returns:
                boolean
        """

        settings = current.deployment_settings
        if not settings.get_auth_email_unlock():
            return False

        mailer = self.settings.mailer
        if not mailer or not mailer.settings.server:
            return False

        if not user or not user.email:
            return False

        return bool(getattr(user, "email_verified", False))

    # -------------------------------------------------------------------------
    def handle_failed_login(self, user=None):
        """
            Handles failed logins:
                - preliminarily locks the account after the 1st threshold
                - hard-locks the account after the 2nd threshold

            Args:
                user: the user record (or None)

            Notes:
                - the lock timeout applies to hard locks
                - ADMIN accounts always get a lock timeout on hard lock
                - invalidates pending unlock tokens on further failures
                - additionally invalidates the session to interrupt serial
                  login failures against hard-locked accounts
        """

        session = current.session
        deployment_settings = current.deployment_settings
        messages = self.messages

        max_failed_logins = deployment_settings.get_auth_max_failed_logins()
        hard_threshold = deployment_settings.get_auth_max_failed_logins_hard()
        lock_timeout = deployment_settings.get_auth_failed_login_lock_timeout()

        if user and max_failed_logins:

            prev_hard = user.registration_key == LOCKED
            prev_prelim = user.locked
            hard_locking = False
            prelim_locking = False

            failed_attempts = (user.failed_attempts or 0) + 1
            update = {"failed_attempts": failed_attempts}

            # Invalidate any pending unlock token
            if user.reset_password_key:
                update["reset_password_key"] = ""

            if failed_attempts >= hard_threshold:
                db = current.db
                ADMIN = self.get_system_roles().ADMIN

                mtable = db.auth_membership
                query = (mtable.user_id == user.id) & \
                        (mtable.group_id == ADMIN) & \
                        (mtable.deleted == False)
                is_admin = db(query).select(mtable.id, limitby=(0, 1)).first() is not None

                if not lock_timeout and is_admin:
                    lock_timeout = 300 # seconds

                if lock_timeout:
                    locked_until = datetime.datetime.utcnow() + \
                                   datetime.timedelta(seconds=lock_timeout)
                else:
                    locked_until = None

                hard_locking = not prev_hard
                update["registration_key"] = LOCKED
                update["locked"] = True
                update["locked_until"] = locked_until

                if failed_attempts > hard_threshold + 3:
                    session.invalid = True
                    session.error = messages.login_attempts_exceeded
                    update["failed_attempts"] = hard_threshold

            elif failed_attempts >= max_failed_logins:
                prelim_locking = not prev_prelim and not prev_hard
                update["locked"] = True
                update["registration_key"] = None
                update["locked_until"] = None

            else:
                update["locked"] = False
                update["registration_key"] = None
                update["locked_until"] = None

            user.update_record(**update)

            if hard_locking:
                self.log_event(self.messages.user_locked_log, user)
                self.send_user_locked_email(user)
            elif prelim_locking:
                self.log_event(self.messages.user_prelim_locked_log, user)

    # -------------------------------------------------------------------------
    def handle_correct_password_while_locked(self, user):
        """
            Handle a correct password entered while the account is
            preliminarily locked: send unlock email if eligible

            Args:
                user: the auth_user Row

            Returns:
                boolean - True if unlock email was sent
        """

        if not self.is_user_preliminarily_locked(user):
            return False

        if self.can_send_unlock_email(user):
            return self.send_account_unlock_email(user)

        return False

    # -------------------------------------------------------------------------
    def unlock_user(self, user, log=None, notify=False):
        """
            Unlocks a previously locked user account

            Args:
                user: the user record
                log: the message to write to the auth_event log
                notify: notify the user about the unlocking

            Note:
                Logging and notification should only happen if
                the unlocking is an explicit action by a user,
                but not if it happens as an implied rule of a
                successful login
        """

        if user:

            update = {}

            if user.registration_key == LOCKED or user.locked:
                update["registration_key"] = None
                update["locked"] = False
            else:
                log = notify = False
            if "failed_attempts" not in user or user.failed_attempts:
                update["failed_attempts"] = 0
            if "locked_until" not in user or user.locked_until:
                update["locked_until"] = None
            if user.reset_password_key:
                update["reset_password_key"] = ""

            if update:
                table = self.settings.table_user
                current.db(table.id == user.id).update(**update)

                user.update(update)

                if log:
                    self.log_event(log, user)

                if notify:
                    self.send_user_unlocked_email(user)

    # -------------------------------------------------------------------------
    def send_account_unlock_email(self, user):
        """
            Send an email with link/code to lift a preliminary lock

            Args:
                user: the auth_user record (Row)

            Returns:
                True if email sent successfully, else False
        """

        mailer = self.settings.mailer
        if not mailer or not mailer.settings.server:
            return False

        messages = self.messages
        system_name = current.deployment_settings.get_system_name()

        key = str(uuid4())
        code = uuid4().hex[-6:].upper()
        token = "%d:%s" % (int(time.time()), self.keyhash(key, code))
        user.update_record(reset_password_key = token)

        url = URL(c = "default",
                  f = "user",
                  args = ["verify_unlock", key],
                  scheme = True)

        subject = messages.unlock_email_subject % {"system_name": system_name}
        message = messages.unlock_email % {"system_name": system_name,
                                           "url": url,
                                           "code": code,
                                           }

        return bool(mailer.send(to = user.email,
                                subject = subject,
                                message = message,
                                ))

    # -------------------------------------------------------------------------
    def send_user_locked_email(self, user):
        """
            Send an email to the user when their account is hard-locked
                - due to excessive failed login attempts

            Args:
                user: the auth_user record (Row)

            Returns:
                True if email sent successfully, else False
        """

        mailer = self.settings.mailer
        if not mailer or not mailer.settings.server:
            return False

        messages = self.messages
        system_name = current.deployment_settings.get_system_name()

        subject = messages.locked_email_subject % {"system_name": system_name}
        message = messages.locked_email % {"system_name": system_name}
        return bool(mailer.send(to = user.email,
                                subject = subject,
                                message = message,
                                ))

    # -------------------------------------------------------------------------
    def send_user_unlocked_email(self, user):
        """
            Send an email to the user when their account is unlocked
                - after being locked due to excessive failed login attempts

            Args:
                user: the auth_user record (Row)

            Returns:
                True if email sent successfully, else False
        """

        mailer = self.settings.mailer
        if not mailer or not mailer.settings.server:
            return False

        messages = self.messages
        system_name = current.deployment_settings.get_system_name()

        subject = messages.unlocked_email_subject % {"system_name": system_name}
        message = messages.unlocked_email % {"system_name": system_name}
        return bool(mailer.send(to = user.email,
                                subject = subject,
                                message = message,
                                ))

    # -------------------------------------------------------------------------
    def verify_unlock_token(self, user, key, code):
        """
            Validate an unlock token and check whether it has expired

            Args:
                user: the auth_user Row
                key: the unlock key from the URL
                code: the activation code from the form

            Returns:
                boolean
        """

        token = user.reset_password_key
        if not token:
            return False

        timeout = current.deployment_settings.get_auth_unlock_token_timeout()
        stored_hash = token
        if ":" in token:
            timestamp, stored_hash = token.split(":", 1)
            try:
                if int(time.time()) - int(timestamp) > timeout:
                    return False
            except ValueError:
                return False

        return stored_hash == self.keyhash(key, code)

# END =========================================================================
