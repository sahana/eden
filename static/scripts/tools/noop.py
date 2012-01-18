#!/usr/bin/python

# This is a no-op script to allow a migration to occur

# Needs to be run in the web2py environment
# python web2py.py -S eden -M -R applications/eden/static/scripts/tools/noop.py

# Load all Models
s3db.load_all_models()