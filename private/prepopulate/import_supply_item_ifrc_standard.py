# Script to import all
#
# run as python web2py.py -S eden -M -R applications/eden/private/prepopulate/import_eric2.py
#

import time

secs = time.mktime(time.localtime())

# Override authorization
auth.override = True
session.s3.roles.append(ADMIN)

s3mgr.load("supply_item")

import_dir = os.path.join(request.folder, "static", "formats", "s3csv")

import_file = os.path.join(import_dir, "eric_supply_item_category.csv")
stylesheet = os.path.join(import_dir, "eric_supply_item_category.xsl")
resource = s3mgr.define_resource("supply", "item_category")
File = open(import_file, "r")
resource.import_xml(File,
                    format="csv",
                    stylesheet=stylesheet)
File.close()

# 500 Items
#import_file = os.path.join(import_dir, "eric_sample.csv")
import_file = os.path.join(import_dir, "eric_complete.csv")
stylesheet = os.path.join(import_dir, "eric.xsl")
resource = s3mgr.define_resource("supply", "item")
File = open(import_file, "r")
resource.import_xml(File,
                    format="csv",
                    stylesheet=stylesheet)
File.close()

db.commit()

print "Total Time: %s" % (time.mktime(time.localtime()) - secs)
