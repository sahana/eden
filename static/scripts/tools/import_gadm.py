# Script to import all countries in Asia Pacific (except Timor Leste, for which we use the UN dataset)
#
# run as python web2py.py -S eden -M -R applications/eden/static/scripts/tools/import_gadm.py
#

import time

secs = time.mktime(time.localtime())

# Asia Pacific less TL
countries = [ "AF", "AU", "BD", "BN", "CK", "CN", "FJ", "FM", "HK", "ID", "IN", "JP", "KH", "KI", "KP", "KR", "LA", "MH", "MM", "MN", "MV", "MY", "NP", "NZ", "PG", "PH", "PK", "PW", "SB", "SG", "SL", "TH", "TO", "TV", "TW", "VN", "VU", "WS"]

gis.import_admin_areas(countries=countries)

db.commit()

print "Total Time: %s" % (time.mktime(time.localtime()) - secs)
