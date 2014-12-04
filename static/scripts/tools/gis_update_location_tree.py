#!/usr/bin/python

# This is a script to update the Location Tree in the Database

# Needs to be run in the web2py environment
# python web2py.py -S eden -M -R applications/eden/static/scripts/tools/gis_update_location_tree.py

s3db.gis_location
gis.update_location_tree()
db.commit()
