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

from s3.s3utils import S3CustomController

THEME = "OCHAROCCA"

# Compact JSON encoding
SEPARATORS = (",", ":")

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        # Calculate summary data (this should be moved - perhaps done async)
        s3db = current.s3db
        db = current.db

        levels = ("L0", "L1", "L2")
        data = {}
        data["total"] = {"location": 0}
        data["total"]["event_event"] = 0
        for level in levels:
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

            # Places
            base_query = (ltable.L0 == name)
            count = db(base_query).count()
            data[code]["location"] = count
            data["total"]["location"] += count

            # Demographic Data 
            for table, tablename in ((ddtable, "stats_demographic_data"), (vdtable, "vulnerability_data")):

                count_field = table._id.count()
                query = base_query & \
                        (level_field.belongs(levels)) & \
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
            query = base_query & \
                    (ltable.id == eltable.location_id) & \
                    (eltable.event_id == etable.id)
            row = db(query).select(count_field,
                                   limitby=(0, 1)).first()
            count = row[count_field]
            data[code]["event_event"] = count
            data["total"]["event_event"] += count

        current.response.data = json.dumps(data, separators=SEPARATORS)

        output = {}
        self._view(THEME, "index.html")
        return output

# END =========================================================================