# -*- coding: utf-8 -*-

from gluon import current
#from gluon.html import *
from gluon.storage import Storage

from s3 import S3CustomController

THEME = "CRMT"

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

        #gtable = s3db.gis_location
        #query &= (atable.location_id == gtable.id)
        ogtable = s3db.org_group
        ltable = s3db.project_activity_group
        query &= (atable.id == ltable.activity_id) & \
                 (ogtable.id == ltable.group_id)
        rows = db(query).select(atable.id,
                                atable.name,
                                atable.date,
                                #gtable.L3,
                                ogtable.name,
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
                                             org_group = row["org_group.name"],
                                             #location = row["gis_location.L3"],
                                             ))
        output["latest_activities"] = latest_activities

        # Which Map should we link to in "Know your community"?
        auth = current.auth
        table = s3db.gis_config
        if auth.is_logged_in() and auth.user.org_group_id:
            # Coalition Map
            ogtable = s3db.org_group
            og = db(ogtable.id == auth.user.org_group_id).select(ogtable.pe_id,
                                                                 limitby=(0, 1)
                                                                 ).first()
            query = (table.pe_id == og.pe_id)
        else:
            # Default Map
            query = (table.uuid == "SITE_DEFAULT")

        config = db(query).select(table.id,
                                  limitby=(0, 1)
                                  ).first()

        try:
            output["config_id"] = config.id
        except:
            output["config_id"] = None

        self._view(THEME, "index.html")
        return output

# END =========================================================================
