# Script to import all
#
# run as python web2py.py -S eden -M -R applications/eden/private/prepopulate/import_supply_item_ifrc_standard.py
#
# Equivalent to PrePop:
# supply,item_category,supply_item_category_ifrc_standard.csv,item_category_ifrc_standard.xsl  
# supply,item,supply_item_ifrc_standard.csv, item_ifrc_standard.xsl

import time

secs = time.mktime(time.localtime())

# Override authorization
auth.override = True
session.s3.roles.append(ADMIN)

s3mgr.load("supply_item")

stylesheet_dir = os.path.join(request.folder, "static", "formats", "s3csv", "supply")
import_dir = os.path.join(request.folder, "private", "prepopulate", "demo", "Standard")

import_file = os.path.join(import_dir, "supply_item_category_ifrc_standard.csv")
stylesheet = os.path.join(stylesheet_dir, "item_category_ifrc_standard.xsl")
resource = s3mgr.define_resource("supply", "item_category")
File = open(import_file, "r")
resource.import_xml(File,
                    format="csv",
                    stylesheet=stylesheet)
File.close()
import_file = os.path.join(import_dir, "supply_item_ifrc_standard_sample.csv") # Sample of 100 Items
#import_file = os.path.join(import_dir, "supply_item_eic.csv") # EIC ~3,000 Items
#import_file = os.path.join(import_dir, "supply_item_ifrc_standard.csv") # Complete ~11,000 Items
stylesheet = os.path.join(stylesheet_dir, "item_ifrc_standard.xsl")
resource = s3mgr.define_resource("supply", "item")
File = open(import_file, "r")
resource.import_xml(File,
                    format="csv",
                    stylesheet=stylesheet)
File.close()

db.commit()

print "Total Time: %s" % (time.mktime(time.localtime()) - secs)
