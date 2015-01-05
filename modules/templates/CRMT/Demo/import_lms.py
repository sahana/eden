# Import LMS Facilities
#
#
# run as python web2py.py -S eden -M -R applications/eden/modules/templates/CRMT/Demo/import_lms.py
#

import os

# Don't add these entries into Audit
settings.security.audit_write = False

# Impersonate as the import user
table = db.auth_user
user_id = db(table.email == "lms@cio.lacounty.gov").select().first().id
auth.s3_impersonate(user_id)

# Don't barf on invalid data
settings.gis.check_within_parent_boundaries = False

# Allow import of non-std Phone data
s3db.org_organisation.phone.requires = None
table = s3db.org_facility
table.phone1.requires = None

# Don't default the Org
table.organisation_id.default = None

# Import Orgs
resource = s3db.resource("org_organisation")
stylesheet = os.path.join(request.folder, "static", "formats", "s3csv", "org", "organisation.xsl")
filename = os.path.join(request.folder, "modules", "templates", "CRMT", "Demo", "LMS_sample_orgs.csv")
File = open(filename, "r")
resource.import_xml(File, format="csv", stylesheet=stylesheet)

# Commit: separate transaction
db.commit()
