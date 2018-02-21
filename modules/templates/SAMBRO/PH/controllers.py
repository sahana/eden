# -*- coding: utf-8 -*-

from gluon import current
from gluon.html import *

from s3 import S3CustomController, s3_str

from templates.SAMBRO.controllers import index, subscriptions, user_info, alert_hub_cop

# -----------------------------------------------------------------------------
class alert_map(index):
    pass

# -----------------------------------------------------------------------------
class index(alert_hub_cop):
    pass

# -----------------------------------------------------------------------------
class bulletin_ocd(S3CustomController):
    """ Generate the Bulletin for OCD """

    def __call__(self):
        """ Main entry point, configuration """

        r = current.request

        alert_id = r.vars.get("alert_id")
        if not alert_id:
            return "alert id is required to generate report"

        language = r.vars.get("lan", "en-US")
        current.response.view = "../modules/templates/SAMBRO/PH/views/bulletin_ocd.html"
        s3db = current.s3db
        table = s3db.cap_alert
        itable = s3db.cap_info
        atable = s3db.cap_area
        ptable = s3db.cap_info_parameter
        query = (table.id == alert_id) & \
                (table.deleted != True) & \
                (itable.alert_id == table.id) & \
                (itable.deleted != True) & \
                (itable.language == language) & \
                (atable.alert_id == table.id) & \
                (atable.deleted != True) & \
                (ptable.info_id == itable.id) & \
                (ptable.deleted != True)

        arows = current.db(query).select(table.status,
                                         table.source,
                                         itable.description,
                                         itable.instruction,
                                         itable.headline,
                                         itable.contact,
                                         ptable.name,
                                         ptable.value)
        parameter_table = TABLE(_style="width: 90%; margin:0 auto")
        if len(arows):
            settings = current.deployment_settings
            parameters = {}
            row_info = arows.first().cap_info
            row_alert = arows.first().cap_alert
            for arow in arows:
                name = arow.cap_info_parameter.name
                if "sahana:bulletin" in name:
                    parameter_table_row = TR(TD(B(name.split("sahana:bulletin:", 1)[1]),
                                                _style="border: 1px solid grey",
                                                ),
                                             TD(arow.cap_info_parameter.value,
                                                _style="border: 1px solid grey",
                                                ))
                    parameter_table.append(parameter_table_row)
    
            output = dict(instruction=s3_str(row_info.instruction),
                          description=s3_str(row_info.description),
                          headline=s3_str(row_info.headline),
                          status=s3_str(row_alert.status),
                          time=s3_str(r.utcnow.strftime("%d %B %Y, %I:%M %p")),
                          source=s3_str(row_alert.source),
                          parameter_table=parameter_table,
                          contact=s3_str(row_info.contact),
                          releasing_officer=settings.get_cap_bulletin_officer(),
                          releasing_officer_designation=settings.get_cap_bulltin_officer_designation(),
                          )
    
            return output
        return "No parameter with sahana:bulletin:"
