# -*- coding: utf-8 -*-

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import current
from gluon.html import *
from gluon.storage import Storage

from s3 import S3CustomController

THEME = "OCHAROCCA"

# Compact JSON encoding
SEPARATORS = (",", ":")

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        # Calculate summary data (this should be moved - perhaps done async)
        db = current.db
        s3db = current.s3db

        levels = ("L0", "L1", "L2", "L3", "L4")
        data = {}
        data["total"] = {"location": 0}
        data["total"]["event_event"] = 0
        for level in levels:
            data["total"]["gis_location_%s" % level] = 0
            data["total"]["stats_demographic_data_%s" % level] = 0
            data["total"]["vulnerability_data_%s" % level] = 0

        ltable = s3db.gis_location
        level_field = ltable.level
        etable = s3db.event_event
        eltable = s3db.event_event_location
        ddtable = s3db.stats_demographic_data
        vdtable = s3db.vulnerability_data

        # @ToDo: FIX!
        for country in current.response.countries:
            code = country["code"]
            name = country["name"]

            data[code] = {}
            base_query = (ltable.L0 == name)

            # Places
            count = db(base_query).count()
            data[code]["location"] = count
            data["total"]["location"] += count

            # Administrative Areas, Demographic Data, Baseline
            for table, tablename in ((ltable, "gis_location"),
                                     (ddtable, "stats_demographic_data"),
                                     (vdtable, "vulnerability_data")):

                count_field = table._id.count()

                query = base_query & \
                        (level_field.belongs(levels))
                if tablename != "gis_location":
                    query = (query) & \
                        (ltable.id == table.location_id)
                rows = db(query).select(level_field,
                                        count_field,
                                        groupby=level_field)
                for row in rows:
                    level = row[level_field]
                    count = row[count_field]
                    data[code]["%s_%s" % (tablename, level)] = count
                    data["total"]["%s_%s" % (tablename, level)] += count

            # Disasters
            count_field = etable._id.count()
            loc_field = eltable.location_id
            query = base_query & \
                    (ltable.id == loc_field) & \
                    (eltable.event_id == etable.id)
            row = db(query).select(count_field,
                                   orderby = None, # Needed for Postgres
                                   ).first()
            if row:
                count = row[count_field]
                data[code]["event_event"] = count
                data["total"]["event_event"] += count

        s3 = current.response.s3
        script = '''homepage_data=%s''' % json.dumps(data, separators=SEPARATORS)
        s3.js_global.append(script)
        script = "/%s/static/themes/%s/js/homepage.js" % \
            (current.request.application, THEME)
        s3.scripts.append(script)

        output = {}
        self._view(THEME, "index.html")
        return output

# END =========================================================================