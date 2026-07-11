"""
    User Account Management

    Copyright: 2024-2024 (c) Sahana Software Foundation

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

__all__ = ("ManageUserAccount",
           )

from gluon import current, URL, redirect

from .base import CRUDMethod

# =============================================================================
class ManageUserAccount(CRUDMethod):

    def apply_method(self, r, **args):

        method = r.method

        # Check for record ID
        user_id = r.id
        if not user_id:
            r.error(400, current.ERROR.BAD_RECORD)

        # TODO consider to redirect to the record
        self.next = URL(args=[], vars={})

        if method == "disable":
            self.disable_user(r, **args)
        elif method == "enable":
            self.enable_user(r, **args)
        elif method == "approve":
            self.approve_user(r, **args)
        elif method == "link":
            self.link_user(r, **args)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        # TODO refactor as strict POST
        if r.http != "POST":
            redirect(self.next)

        return current.xml.json_message()

    # -------------------------------------------------------------------------
    def disable_user(self, r, **args):
        """ Disable a user account """

        T = current.T

        db = current.db
        s3db = current.s3db
        auth = current.auth
        session = current.session

        tablename = auth.settings.table_user_name
        table = auth.settings.table_user

        user_id = r.id
        if user_id == session.auth.user.id:
            # Must not disable current user
            r.error(400, T("Cannot disable your own account!"), next=self.next)

        # Invoke ondisable hook
        ondisable = s3db.get_config(tablename, "ondisable")
        if callable(ondisable):
            ondisable(user_id)

        # Disable user account
        db(table.id == user_id).update(registration_key = "disabled")

        # Log event
        auth.log_event(auth.messages.user_disabled_log, {"user_id": user_id})

        # Confirm
        session.confirmation = T("User Account has been Disabled")

    # -------------------------------------------------------------------------
    def enable_user(self, r, **args):
        """ Re-enable a disabled|blocked|failed user account """

        T = current.T
        auth = current.auth

        # Check user account
        user = r.record
        if user.registration_key not in ("disabled", "blocked", "failed"):
            r.error(400, T("User Account not Disabled"), next=self.next)

        # Enable/unlock user account
        user.update_record(registration_key = None,
                           failed_attempts = 0,
                           locked = False,
                           locked_until = None,
                           )

        # Log event
        auth.log_event(auth.messages.user_enabled_log, {"user_id": user.id})

        current.session.confirmation = T("User Account has been Re-enabled")

    # -------------------------------------------------------------------------
    def approve_user(self, r, **args):
        """ Approve a pending user account """

        T = current.T
        s3db = current.s3db
        auth = current.auth

        user = r.record

        approve_user = s3db.get_config("auth_user", "approve_user")
        if callable(approve_user):
            # Use custom approval method
            approve_user(r, **args)

        else:
            auth.s3_approve_user(user)
            self.next = URL(args=[r.id, "roles"])

        auth.log_event(auth.messages.user_enabled_log, {"user_id": user.id})

        current.session.confirmation = T("User Account has been Approved")

    # -------------------------------------------------------------------------
    def link_user(self, r, **args):
        """ Link a user account to person/staff records """

        T = current.T

        # Link account to person/staff record
        current.auth.s3_link_user(r.record)

        current.session.confirmation = T("User has been (re)linked to Person and Human Resource record")

# END =========================================================================
