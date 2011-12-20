# -*- coding: utf-8 -*-
import cPickle as pickle
import csv

# This script processes import_job records from the admin module that are in the
# 'processing' state. This indicates that the user has matched up the columns
# and the records are ready to be validated and prepared for import.
#

jobs = db(db.admin_import_job.status == 'processing').select()
for job in jobs:
    # Get job column map.
    try:
        column_map = pickle.loads(job.column_map)
    except pickle.UnpicklingError:
        column_map = []
    
    # Create a form to use for validation.
    form = SQLFORM(db['%s_%s' % (job.module, job.resource)])

    # Open the input file.
    filepath = os.path.join(request.folder, 'uploads', job.source_file)
    reader = csv.reader(open(filepath, 'r'))
    
    # Retrieve column headings from the first line.
    csv_headings = []
    for line in reader:
        for col in line:
            csv_headings.append(col)
        break
    if csv_headings != [t[0] for t in column_map]:
        print 'Cannot process job #%d. Column headings do not match DB!' % job.id
        continue

    # Read each line
    valid_lines = 0
    for line_num, line in enumerate(reader, 0):
        line_data = {}
        # Map CSV headers to model fields.
        for idx, col in enumerate(line):
            field = column_map[idx][1]
            if not field:
                continue
            line_data[field] = col
        # Validate data via the SQLFORM instance.
        validate_data = line_data.copy()
        validate_data.update({'_formname': 'import'})
        valid = form.accepts(validate_data, None, formname='import',
                             dbio=False)
        # store into an ImportLine model.
        db_data = dict(
                import_job=job.id,
                line_no=line_num + 2,  # +2 (zero offset + header line).
                data=pickle.dumps(line_data, pickle.HIGHEST_PROTOCOL),
                valid=valid,
                )
        if valid:
            db_data.update(errors=None, status='import')
            valid_lines += 1
        else:
            db_data.update(
                    errors='Invalid Fields: %s' % ', '.join(form.errors),
                    status='ignore')
        db.admin_import_line.insert(**db_data)

    # Update job status.
    if valid_lines:
        db(db.admin_import_job.id==job.id).update(status='processed')
    else:
        db(db.admin_import_job.id==job.id).update(
                status='failed',
                failure_reason='no valid lines in file'
                )

# Explicitly commit DB operations when running from Cron
db.commit()
