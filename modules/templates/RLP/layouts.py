"""
    Menu layouts for RLP

    License: MIT
"""

__all__ = ("S3OrgMenuLayout",
           "OM",
           )

from gluon import current, IMG
from core import S3NavigationItem

# =============================================================================
class S3OrgMenuLayout(S3NavigationItem):
    """ Layout for the organisation-specific menu """

    @staticmethod
    def layout(item):

        name = "Rheinland-Pfalz"

        current_user = current.auth.user
        if current_user:
            user_org_id = current_user.organisation_id
            if user_org_id:
                otable = current.s3db.org_organisation
                query = (otable.id == user_org_id) & \
                        (otable.deleted == False)
                row = current.db(query).select(otable.name,
                                               limitby = (0, 1),
                                               ).first()
                if row:
                    name = row.name

        logo = IMG(_src = "/%s/static/themes/RLP/img/logo_rlp.png" %
                          current.request.application,
                   _alt = name,
                   _height = 49,
                   )

        # Note: render using current.menu.org.render()[0] + current.menu.org.render()[1]
        return (name, logo)

# -----------------------------------------------------------------------------
# Shortcut
OM = S3OrgMenuLayout

# END =========================================================================
