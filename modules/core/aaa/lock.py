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

from gluon import current, URL
from uuid import uuid4

LOCKED = "failed"

# =============================================================================
class AccountLockingMixin:
    """ Auth mixin to handle locking of accounts """

    def is_user_locked(self, user):
        """
            Checks whether a user account is (still) locked

            Args:
                user: the user account (auth_user Row)

            Returns:
                boolean
        """

        if not user or user.registration_key != LOCKED:
            return False

        return not user.locked_until or user.locked_until > current.request.utcnow

    # -------------------------------------------------------------------------
    def handle_failed_login(self, user=None):
        """
            Handles failed logins:
                - locks the user account when there are too many failed login
                  attempts (possibly with a lock timeout, if configured)

            Args:
                user: the user record (or None)

            Notes:
                - the lock timeout progresses for every further attempt to
                  login to a locked account
                - ADMIN accounts always get a lock timeout, even when other
                  accounts are locked indefinitely
                - additionally invalidates the session to interrupt serial
                  login failures
        """

        session = current.session
        deployment_settings = current.deployment_settings
        messages = self.messages

        # Get the Auth Lock settings
        max_failed_logins = deployment_settings.get_auth_max_failed_logins()
        lock_timeout = deployment_settings.get_auth_failed_login_lock_timeout()

        # Check if the Failed Login Count is greater than 0 (0 means no lock policy)
        if user and max_failed_logins:

            prev = user.registration_key == LOCKED
            locking = False

            failed_attempts = (user.failed_attempts or 0) + 1
            update = {"failed_attempts": failed_attempts}

            if failed_attempts >= max_failed_logins:
                # Mandatory lock-timeout for ADMIN accounts
                # Check directly in database since user is not logged in yet
                db = current.db
                ADMIN = self.get_system_roles().ADMIN
             

                mtable = db.auth_membership
                query = (mtable.user_id == user.id) & \
                        (mtable.group_id == ADMIN) & \
                        (mtable.deleted == False)
                is_admin = db(query).select(mtable.id, limitby=(0, 1)).first() is not None

                if not lock_timeout and is_admin:
                    lock_timeout = 300 # seconds
                # Determine lock-timeout
                if lock_timeout:
                    locked_until = datetime.datetime.utcnow() + \
                                   datetime.timedelta(seconds=lock_timeout)
                else:
                    locked_until = None

                locking = not prev
                update["registration_key"] = LOCKED
                update["locked_until"] = locked_until

                if failed_attempts > max_failed_logins + 3:
                    # User is ignoring the lock => interrupt their flow
                    # by invalidating the session
                    session.invalid = True
                    session.error = messages.login_attempts_exceeded
                    update["failed_attempts"] = max_failed_logins
            else:
                update["registration_key"] = None
                update["locked_until"] = None

            user.update_record(**update)

            if locking:
                # Log the event
                self.log_event(self.messages.user_locked_log, user)
                # Notify the user by email
                self.send_user_locked_email(user)

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

            if user.registration_key == LOCKED:
                update["registration_key"] = None
            else:
                log = notify = False
            if "failed_attempts" not in user or user.failed_attempts:
                update["failed_attempts"] = 0
            if "locked_until" not in user or user.locked_until:
                update["locked_until"] = None

            if update:
                table = self.settings.table_user
                current.db(table.id == user.id).update(**update)

                user.update(update)

                # Log the event
                if log:
                    self.log_event(log, user)

                # Notify the user by email
                if notify:
                    self.send_user_unlocked_email(user)

    # -------------------------------------------------------------------------
    def send_user_locked_email(self, user):
        """
            Send an email to the user when their account is locked
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
        settings = current.deployment_settings

        subject = messages.locked_email_subject % {"system_name": system_name}
        message = messages.locked_email % {"system_name": system_name}

        if settings.get_auth_email_unlock():
            key = str(uuid4())
            code = uuid4().hex[-6:].upper()
            user.update_record(reset_password_key = self.keyhash(key, code))
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

# END =========================================================================
