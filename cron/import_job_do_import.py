# -*- coding: utf-8 -*-
import cPickle as pickle

# This script processes import_job records from the admin module that are in the
# 'import' state. This indicates that the lines have been validated, and the user
# has selected any to be ignored, the remaining lines should be imported.
#

jobs = db(db.admin_import_job.status == 'import').select()
for job in jobs:
    # Create a form to use for validation and insertion.
    form = SQLFORM(db['%s_%s' % (job.module, job.resource)])

    # Loop over each line flagged for import
    lines = db((db.admin_import_line.import_job==job.id) &
               (db.admin_import_line.status == 'import')).select()
    imported_lines = 0
    failed_lines = 0
    for line in lines:
        if not line.valid:
            # Skip invalid lines.
            failed_lines += 1
            continue

        # Extract pickled data.
        try:
            data = pickle.loads(line.data)
        except pickle.UnpicklingError:
            failed_lines += 1
            db.admin_import_line[line.id] = dict(
                    errors = 'Could not unpickle data')
            continue
        
        # Try and insert.
        data.update({'_formname': 'import'})
        if form.accepts(data, None, formname='import'):
            db.admin_import_line[line.id] = dict(
                    status = 'imported',
                    errors = None)
            imported_lines += 1
        else:
            db.admin_import_line[line.id] = dict(
                    errors = 'Import Failed: %s' % ', '.join(form.errors))
            failed_lines += 1


    # Update job status.
    if not failed_lines:
        db(db.admin_import_job.id==job.id).update(status='imported')
    else:
        # If one or more lines failed, put back into processed state,
        # for user to examine further.
        db(db.admin_import_job.id==job.id).update(status='processed')

# Explicitly commit DB operations when running from Cron
db.commit()
