"""
    Custom Controllers for DRKCM

    License: MIT
"""

from gluon import current, DIV, H3, H4, I, LI, P, TAG, UL, XML

from core import FS, CustomController

THEME = "DRK"

# =============================================================================
class index(CustomController):
    """ Custom Home Page """

    def __call__(self):

        output = {}

        T = current.T

        auth = current.auth
        settings = current.deployment_settings


        # Defaults
        login_form = None
        login_div = None
        announcements = None
        announcements_title = None

        roles = current.session.s3.roles
        sr = auth.get_system_roles()
        if sr.AUTHENTICATED in roles:
            # Logged-in user
            # => display announcements
            from s3db.cms import cms_Announcements
            announcements = cms_Announcements().html()
            if announcements:
                announcements_title = T("Announcements")
        else:
            # Anonymous user
            # => provide a login box
            login_div = DIV(H3(T("Login")),
                            )
            auth.messages.submit_button = T("Login")
            login_form = auth.login(inline=True)

        output = {"login_div": login_div,
                  "login_form": login_form,
                  "announcements": announcements,
                  "announcements_title": announcements_title,
                  }

        # Custom view and homepage styles
        self._view(settings.get_theme_layouts(), "index.html")

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def get_announcements(roles=None):
        """
            Get current announcements

            Args:
                roles: filter announcement by these roles

            Returns:
                any announcements (Rows)
        """

        db = current.db
        s3db = current.s3db

        # Look up all announcements
        ptable = s3db.cms_post
        stable = s3db.cms_series
        join = stable.on((stable.id == ptable.series_id) & \
                         (stable.name == "Announcements") & \
                         (stable.deleted == False))
        query = (ptable.date <= current.request.utcnow) & \
                (ptable.expired == False) & \
                (ptable.deleted == False)

        if roles:
            # Filter posts by roles
            ltable = s3db.cms_post_role
            q = (ltable.group_id.belongs(roles)) & \
                (ltable.deleted == False)
            rows = db(q).select(ltable.post_id,
                                cache = s3db.cache,
                                groupby = ltable.post_id,
                                )
            post_ids = {row.post_id for row in rows}
            query = (ptable.id.belongs(post_ids)) & query

        posts = db(query).select(ptable.name,
                                 ptable.body,
                                 ptable.date,
                                 ptable.priority,
                                 join = join,
                                 orderby = (~ptable.priority, ~ptable.date),
                                 limitby = (0, 5),
                                 )

        return posts

# =============================================================================
class userstats(CustomController):
    """
        Custom controller to provide user account statistics per
        root organisation (for accounting in a shared instance)
    """

    def __init__(self):

        super().__init__()

        self._root_orgs = None
        self._stats = None

    # -------------------------------------------------------------------------
    def __call__(self):
        """ The userstats controller """

        # Require ORG_GROUP_ADMIN
        auth = current.auth
        if not auth.s3_has_role("ORG_GROUP_ADMIN"):
            auth.permission.fail()

        from core import BasicCRUD, s3_get_extension, crud_request

        request = current.request
        args = request.args

        # Create an CRUDRequest
        r = crud_request("org", "organisation",
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
        from core import CustomForm, VirtualFormField
        crud_form = CustomForm("name",
                               VirtualFormField("total_accounts",
                                                label = TOTAL,
                                                ),
                               VirtualFormField("active_accounts",
                                                label = ACTIVE,
                                                ),
                               VirtualFormField("disabled_accounts",
                                                label = DISABLED,
                                                ),
                               VirtualFormField("active30",
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
            open_url = BasicCRUD._linkto(r, update=False)("[id]")

            # Add action button for open
            action_buttons = BasicCRUD.action_buttons
            action_buttons(r,
                           deletable = False,
                           copyable = False,
                           editable = False,
                           read_url = open_url,
                           )

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def rheader(r):
        """
            Show the current date in the output

            Args:
                r: the CRUDRequest

            Returns:
                the page header (rheader)
        """

        from core import S3DateTime
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

            Args:
                row: the Row
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

            Args:
                row: the Row
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

            Args:
                row: the Row
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

            Args:
                row: the Row
        """

        if hasattr(row, "org_organisation"):
            row = row.org_organisation

        stats = self.stats.get(row.id)
        return stats["active30"] if stats else 0

# END =========================================================================
