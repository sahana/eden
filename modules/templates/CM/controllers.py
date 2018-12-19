# -*- coding: utf-8 -*-

import json

from os import path

from gluon import current, redirect
from gluon.html import *
from gluon.storage import Storage

from s3 import FS, S3CustomController
from s3theme import formstyle_foundation_inline

THEME = "default"

# =============================================================================
class userstats(S3CustomController):
    """
        Custom controller to provide user account statistics per
        root organisation (for accounting in a shared instance)
    """

    def __init__(self):
        """ Constructor """

        super(userstats, self).__init__()

        self._root_orgs = None
        self._stats = None

    # -------------------------------------------------------------------------
    def __call__(self):
        """ The userstats controller """

        # Require ORG_GROUP_ADMIN
        auth = current.auth
        if not auth.s3_has_role("ORG_GROUP_ADMIN"):
            auth.permission.fail()

        from s3 import S3CRUD, s3_get_extension, s3_request

        request = current.request
        args = request.args

        # Create an S3Request
        r = s3_request("org", "organisation",
                       c = "default",
                       f = "index/%s" % args[0],
                       args = args[1:],
                       extension = s3_get_extension(request),
                       )

        # Filter to root organisations
        resource = r.resource
        resource.add_filter(FS("id").belongs(self.root_orgs))

        # Configure field methods
        from gluon import Field
        table = resource.table
        table.total_accounts = Field.Method("total_accounts", self.total_accounts)
        table.active_accounts = Field.Method("active_accounts", self.active_accounts)
        table.disabled_accounts = Field.Method("disabled_accounts", self.disabled_accounts)
        table.active30 = Field.Method("active30", self.active30)

        # Labels for field methods
        T = current.T
        TOTAL = T("Total User Accounts")
        ACTIVE = T("Active")
        DISABLED = T("Inactive")
        ACTIVE30 = T("Logged-in Last 30 Days")

        # Configure list_fields
        list_fields = ("id",
                       "name",
                       (TOTAL, "total_accounts"),
                       (ACTIVE, "active_accounts"),
                       (DISABLED, "disabled_accounts"),
                       (ACTIVE30, "active30"),
                       )

        # Configure form
        from s3 import S3SQLCustomForm, S3SQLVirtualField
        crud_form = S3SQLCustomForm("name",
                                    S3SQLVirtualField("total_accounts",
                                                      label = TOTAL,
                                                      ),
                                    S3SQLVirtualField("active_accounts",
                                                      label = ACTIVE,
                                                      ),
                                    S3SQLVirtualField("disabled_accounts",
                                                      label = DISABLED,
                                                      ),
                                    S3SQLVirtualField("active30",
                                                      label = ACTIVE30,
                                                      ),
                                    )

        # Configure read-only
        resource.configure(insertable = False,
                           editable = False,
                           deletable = False,
                           crud_form = crud_form,
                           filter_widgets = None,
                           list_fields = list_fields,
                           )

        output = r(rheader=self.rheader)

        if isinstance(output, dict):

            output["title"] = T("User Statistics")

            # URL to open the resource
            open_url = resource.crud._linkto(r, update=False)("[id]")

            # Add action button for open
            action_buttons = S3CRUD.action_buttons
            action_buttons(r,
                           deletable = False,
                           copyable = False,
                           editable = False,
                           read_url = open_url,
                           )

        return output

    # -------------------------------------------------------------------------
    def rheader(self, r):
        """
            Show the current date in the output

            @param r: the S3Request
            @returns: the page header (rheader)
        """

        from s3 import S3DateTime
        today = S3DateTime.datetime_represent(r.utcnow, utc=True)

        return P("%s: %s" % (current.T("Date"), today))

    # -------------------------------------------------------------------------
    @property
    def root_orgs(self):
        """
            A set of root organisation IDs (lazy property)
        """

        root_orgs = self._root_orgs
        if root_orgs is None:

            db = current.db
            s3db = current.s3db

            table = s3db.org_organisation
            query = (table.root_organisation == table.id) & \
                    (table.deleted == False)
            rows = db(query).select(table.id)

            self._root_orgs = root_orgs = set(row.id for row in rows)

        return root_orgs

    # -------------------------------------------------------------------------
    @property
    def stats(self):
        """
            User account statistics per root organisation (lazy property)
        """

        stats = self._stats
        if stats is None:

            db = current.db
            s3db = current.s3db

            utable = s3db.auth_user
            otable = s3db.org_organisation

            left = otable.on(otable.id == utable.organisation_id)

            query = (utable.deleted == False)
            users = db(query).select(otable.root_organisation,
                                     utable.registration_key,
                                     utable.timestmp,
                                     left = left,
                                     )

            # Determine activity period start
            import datetime
            now = current.request.utcnow
            start = (now - datetime.timedelta(days=30)).replace(hour = 0,
                                                                minute = 0,
                                                                second = 0,
                                                                microsecond = 0,
                                                                )

            # Collect stats
            stats = {}
            for user in users:

                account = user.auth_user
                organisation = user.org_organisation

                root_org = organisation.root_organisation
                if not root_org:
                    continue

                if root_org in stats:
                    org_stats = stats[root_org]
                else:
                    org_stats = stats[root_org] = {"total": 0,
                                                   "disabled": 0,
                                                   "active30": 0,
                                                   }

                # Count total accounts
                org_stats["total"] += 1

                # Count inactive accounts
                if account.registration_key:
                    org_stats["disabled"] += 1

                # Count accounts logged-in in the last 30 days
                timestmp = account.timestmp
                if timestmp and timestmp >= start:
                    org_stats["active30"] += 1

            self._stats = stats

        return stats

    # -------------------------------------------------------------------------
    def total_accounts(self, row):
        """
            Field method to return the total number of user accounts
            for the organisation

            @param row: the Row
        """

        if hasattr(row, "org_organisation"):
            row = row.org_organisation

        stats = self.stats.get(row.id)
        return stats["total"] if stats else 0

    # -------------------------------------------------------------------------
    def active_accounts(self, row):
        """
            Field method to return the number of active user accounts
            for the organisation

            @param row: the Row
        """

        if hasattr(row, "org_organisation"):
            row = row.org_organisation

        stats = self.stats.get(row.id)
        if stats:
            result = stats["total"] - stats["disabled"]
        else:
            result = 0
        return result

    # -------------------------------------------------------------------------
    def disabled_accounts(self, row):
        """
            Field method to return the number of disabled user accounts
            for the organisation

            @param row: the Row
        """

        if hasattr(row, "org_organisation"):
            row = row.org_organisation

        stats = self.stats.get(row.id)
        return stats["disabled"] if stats else 0

    # -------------------------------------------------------------------------
    def active30(self, row):
        """
            Field method to return the number of user accounts for the
            organisation which have been used over the past 30 days
            (useful to verify the number of active accounts)

            @param row: the Row
        """

        if hasattr(row, "org_organisation"):
            row = row.org_organisation

        stats = self.stats.get(row.id)
        return stats["active30"] if stats else 0

# END =========================================================================
