# -*- coding: utf-8 -*-

from gluon import *
from s3 import *
from s3layouts import *
try:
    from .layouts import *
except ImportError:
    pass
import s3menus as default

# =============================================================================
class S3MainMenu(default.S3MainMenu):
    """ Custom Application Main Menu """

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        AUTHENTICATED = current.session.s3.system_roles.AUTHENTICATED


        sysname = current.deployment_settings.get_system_name_short()
        return [
            homepage("gis"),
            MM("Incidents", c="event", f="incident_report"),
            homepage("org"),
            MM("Activities", c="project", f="activity", m="summary"),
            MM("Facilities", link=False)(
                homepage("inv"),
                homepage("cr"),
                MM("Hospitals", c="hms", f="hospital"),
                MM("Other Facilities", c="org", f="facility", m="summary"),
            ),
            MM("Manage", link=False, restrict=AUTHENTICATED)(
                MM("Events", c="event", f="event"),
                MM("Requests", c="req", f="req"),
                MM("Inventory", c="inv", f="inv_item"),
                MM("Staff", c="hrm", f="staff", m="summary"),
                MM("Projects", c="project", f="project"),
            ),
        ]

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """ Custom Application Side Menu """

    # -------------------------------------------------------------------------
    @staticmethod
    def project():
        """ PROJECT / Project Module """

        settings = current.deployment_settings
        activities = lambda i: settings.get_project_activities()
        activity_types = lambda i: settings.get_project_activity_types()
        sectors = lambda i: settings.get_project_sectors()

        return M(c="project")(
                M("Projects", f="project")(
                    M("Create", m="create"),
                    ),
                M("Activities", f="activity", check=activities)(
                    M("Create", m="create"),
                    ),
                M("Import", f="project", m="import", p="create")(
                    M("Import Projects", m="import", p="create"),
                    M("Import Project Organizations", f="organisation",
                        m="import", p="create"),
                    ),
                M("Activity Types", f="activity_type", check=activity_types)(
                    M("Create", m="create"),
                    ),
                M("Sectors", f="sector", check=sectors)(
                    M("Create", m="create"),
                    ),
                )

# END =========================================================================
