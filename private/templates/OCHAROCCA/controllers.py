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

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        # Calculate summary data (this should be moved - perhpas done unsync)
        s3db = current.s3db
        db = current.db

        levels = ("L0", "L1","L2")
        data = {}
        data["total"] = {"location": 0}
        data["total"]["event"] = 0
        for level in levels:
            data["total"]["demographic_data_%s" % level] = 0
    
        for country in current.response.countries:
            code = country["code"]
            name = country["name"]
    
            data[code] = {}
    
            ltable = s3db.gis_location
            dtable = s3db.stats_demographic_data
    
            # Places
            query = ltable.L0 == name 
            count = db(query).count()
            data[code]["location"] = db(query).count()
            data["total"]["location"] += count
            
            # Demographic Data 
            level_field = ltable.level
            count_field = ltable._id.count()
            rows = db(query & (level_field.belongs(levels))
                      ).select(level_field, count_field, groupby=level_field)
            for row in rows:
                level = row[level_field]
                count = row[count_field]
                data[code]["demographic_data_%s" % level] = count
                data["total"]["demographic_data_%s" % level] += count
            # Disasters
            count = db(query).count()
            data[code]["event"] = db(query).count()
            data["total"]["event"] += count

        current.response.data = json.dumps(data)

        output = {}
        self._view(THEME, "index.html")
        return output
