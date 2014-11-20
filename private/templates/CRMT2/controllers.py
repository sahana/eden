# -*- coding: utf-8 -*-

from gluon import current
#from gluon.html import *
from gluon.storage import Storage

from s3 import S3CustomController

THEME = "CRMT2"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        output = {}

        # Latest Activities
        db = current.db
        s3db = current.s3db
        atable = s3db.project_activity
        query = (atable.deleted == False)
        output["total_activities"] = db(query).count()

        gtable = s3db.gis_location
        query &= (atable.location_id == gtable.id)
        rows = db(query).select(atable.id,
                                atable.name,
                                atable.date,
                                gtable.L3,
                                limitby = (0, 3),
                                orderby = ~atable.date
                                )
        latest_activities = []
        current.deployment_settings.L10n.date_format = "%d %b %y"
        drepresent = atable.date.represent

        for row in rows:
            date = row["project_activity.date"]
            if date:
                nice_date = drepresent(date)
            else:
                nice_date = ""
            latest_activities.append(Storage(id = row["project_activity.id"],
                                             name = row["project_activity.name"],
                                             date = nice_date,
                                             date_iso = date or "",
                                             location = row["gis_location.L3"],
                                             ))
        output["latest_activities"] = latest_activities

        self._view(THEME, "index.html")
        return output

# END =========================================================================
