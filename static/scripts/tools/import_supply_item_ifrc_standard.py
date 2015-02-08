# Script to import all
#
# run as python web2py.py -S eden -M -R applications/eden/static/scripts/tools/import_supply_item_ifrc_standard.py -A complete
#
# Equivalent to PrePop:
# supply,item_category,supply_item_category_ifrc_standard.csv,item_category_ifrc_standard.xsl
# supply,item,supply_item_ifrc_standard.csv, item_ifrc_standard.xsl

import sys
import time

args = sys.argv
if args[1:]:
    # The 1st argument is taken to be the type
    set = args[1]
else:
    # default to sample
    set = "sample"

secs = time.mktime(time.localtime())

# Override authorization
auth.override = True
session.s3.roles.append(ADMIN)

s3db.table("supply_item")

stylesheet_dir = os.path.join(request.folder, "static", "formats", "s3csv", "supply")
import_dir = os.path.join(request.folder, "private", "templates", "Standard")

import_file = os.path.join(import_dir, "supply_item_category_ifrc_standard.csv")
stylesheet = os.path.join(stylesheet_dir, "item_category_ifrc_standard.xsl")
resource = s3db.resource("supply_item_category")
File = open(import_file, "r")
resource.import_xml(File,
                    format="csv",
                    stylesheet=stylesheet)
File.close()

if set == "sample":
    # Sample of 100 Items
    import_file = os.path.join(import_dir, "supply_item_ifrc_standard_sample.csv")
elif set == "eic":
    # EIC ~3,000 Items
    import_file = os.path.join(import_dir, "supply_item_eic.csv")
elif set == "complete":
    # Complete ~11,000 Items
    import_file = os.path.join(import_dir, "supply_item_ifrc_standard.csv")

stylesheet = os.path.join(stylesheet_dir, "item_ifrc_standard.xsl")
resource = s3db.resource("supply_item")
File = open(import_file, "r")
resource.import_xml(File,
                    format="csv",
                    stylesheet=stylesheet)
File.close()

db.commit()

auth.override = False

print "Total Time: %s" % (time.mktime(time.localtime()) - secs)
