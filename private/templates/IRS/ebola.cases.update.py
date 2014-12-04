# -*- coding: utf-8 -*-
#!/usr/bin/python

# This script does 3 things:
# 1. Downloads the latest copy of the Ebola Cases spreadsheet
# 2. Disaggregates the data to have it not show cumulative cases (we'd rather have aggregation under Sahana's control)
# 3. Convert it to a Sahana Import format
#    - hardest part here is ensuring that Location Names are standardised with http://eden.sahanafoundation.org/wiki/GIS/Data 

# Assumes that the GIS data from the Sahana page is imported

# Needs to be run in the web2py environment:
# cd web2py
# python web2py.py -S eden -M -R applications/eden/private/templates/IRS/ebola.cases.update.py

from time import gmtime, strftime
todays_date = strftime("%Y-%m-%d", gmtime())

# Options which changed for other data sources
SOURCE_URL = "http://data.hdx.rwlabs.org/storage/f/2014-11-14T13%3A55%3A58.796Z/data-ebola-public.xlsx" # Linked from https://data.hdx.rwlabs.org/dataset/rowca-ebola-cases Note timestamp changes daily so no auto-update possible :/
#SOURCE_URL = "http://eden.sahanafoundation.org/downloads/Data%20Ebola%20(Public).xlsx" # For use when site is down (gives a 404 at times, perhaps when file is being updated)
SOURCE_SHEET = "ROWCA Ebola All Sec Review"
OUTPUT_CSV = "ebola_cases_%s.csv" % todays_date

country_codes = {"Guinea": "GN",
                 "Liberia": "LR",
                 "Nigeria": "NG",
                 "Senegal": "SN",
                 "Sierra Leone": "SL",
                 }

location_names = {# GN
                  "Boke": "Boké",
                  "Dubreka": "Dubréka",
                  "Gueckedou": "Guéckédou",
                  "Kerouane": "Kérouané",
                  "Nzerekore": "Nzérékoré",
                  "Telimele": "Télimélé",
                  # SL
                  "Freetown": "Urban",
                  "Western Area": "Western",
                  # SN
                  "Dakar": "Parcelles Assainies", # specific to the 1 current case ;)
                  "District Nord": "Ourossogui", # specific to the 1 current case ;)
                  }
# @ToDo:
# - Allow filtering to just a single country
# - Allow filtering to a range of dates (priority: since xxx to get a diff. NB This is just to save time, since the deduplicator should prevent dupes)
# - Make script more widely usable?: other resources (e.g. Hospitals)

import string
import urllib2
import xlrd

# Open the file from the remote server
# @todo write the remote file to a temp file and then pass to load_workbook
print "Downloading data..."
u = urllib2.urlopen(SOURCE_URL)
wb = xlrd.open_workbook(file_contents=u.read())
ws = wb.sheet_by_name(SOURCE_SHEET)

# Load models
table = s3db.gis_location
otable = s3db.org_organisation

rejected_loc = {}
new_org = {}

# Utility functions
def lookup_loc(location, country):
    """
        Location Names need to match what we have already
    """
    corrected = location_names.get(location)
    if corrected:
        return get_loc_from_db(corrected, country)

    # LR
    if location[-6:] == "County":
        # If the location ends with "County", then strip it out and try again
        return get_loc_from_db(location[:-6].strip(), country)
    # SL
    if location.startswith("Western Area"):
        return get_loc_from_db(location[12:].strip(), country)

    # Log location as being in error
    if location in rejected_loc:
        rejected_loc[location] += 1
    else:
        rejected_loc[location] = 1

def get_loc_from_db(location, country):
    """
        Lookup a Location Hierarchy
    """
    row = db(table.name == location).select(table.level,
                                            table.L1,
                                            table.L2,
                                            table.L3,
                                            orderby=table.level,
                                            limitby=(0, 1)).first()
    if row is None:
        # Name doesn't match
        return lookup_loc(location, country)

    # Will crash if not in lookup which is by-design
    country_code = country_codes[country]

    return (country_code, row.L1, row.L2, row.L3)

def get_org_from_db(org, country):
    """
        Lookup an Organisation
    """

    if org.lower() == "gvt":
        if country == "Guinea":
            return "Ministere de la Sante"
        else:
            return "MoH %s" % country

    if org.startswith("WHO"):
        return "World Health Organisation"

    # Try Name
    row = db(otable.name == org).select(table.id,
                                        limitby=(0, 1)).first()
    if row:
        return org

    # Name doesn't match, try acronym
    row = db(otable.acronym == org).select(table.name,
                                           limitby=(0, 1)).first()
    if row:
        return row.name

    # Log org as being in error
    if org in new_org:
        new_org[org] += 1
    else:
        new_org[org] = 1
    return org

def storeRow(location, row, country):
    """
        Store a row in our data structure
    """
    statistic = row[2].strip()
    if statistic == "New cases":
        # Not needed since we're disaggregating
        return
    value = row[3]
    if value in (None, "", " "):
        value = None
    else:
        value = int(value)
    date_t = xlrd.xldate_as_tuple(row[4], 0)
    date = "%d-%02d-%02d" % (date_t[0], date_t[1], date_t[2])
    source = row[5].strip()
    org = get_org_from_db(source, country)
    if row[6] != None:
        source_url = row[6].strip()
    else:
        source_url = "" 

    if statistic not in statistics:
        statistics[statistic] = {}

    if location not in statistics[statistic]:
        statistics[statistic][location] = {}

    statistics[statistic][location][date] = [value, org, source_url]

def extractRow(row):
    """
        Extract a row from our Source Spreadsheet
    """
    statistic = row[2].strip()
    if statistic == "New cases":
        # Not relevant as we dis-aggregate anyway
        return

    location = row[1].strip()
    # Ignore combined locations
    if location == "National":
        return
    elif " and " in location:
        if location in rejected_loc:
            rejected_loc[location] += 1
        else:
            rejected_loc[location] = 1
        return

    country = row[0].strip()
    if country != "Sierra Leone":
        # This deployment is only interested in SL data
        return

    if not location in location_list:
        # Ensure some standard Capitalisation - or at least try ;)
        location = string.capwords(location)
        loc_row = get_loc_from_db(location, country)
        location_list[location] = loc_row

    if location_list[location] is not None:
        # Now we have verified location data, store the details
        storeRow(location, row, country)


print "Extracting data..."
location_list = {}
statistics = {}

for rcnt in xrange(1, ws.nrows):
    row = ws.row_values(rcnt, 0, 7)
    extractRow(row)


print "Dis-aggregating data..."
rejected_data = {}
suspect_data = {}

def disaggregate(statistic, data):
    """
        Dis-aggregate the running total for each statistic
    """
    #ignored = False
    new_statistic = {}
    for (loc, details) in data.items():
        new_statistic[loc] = {}
        prev_value = 0
        for key in sorted(details.keys()):
            new_value = details[key][0]
            if prev_value != new_value:
                if new_value is None:
                    if prev_value:
                        rejected_data[loc] = [key, "None value", statistic, new_value, prev_value]
                        continue
                    else:
                        new_value = 0
                if (new_value < prev_value) and \
                   (statistic not in ("Suspected cases", "Probable cases")): # and not ignored:
                    # ignore the data value - but never ignore consecutive cases
                    #ignored = True
                    suspect_data[loc] = [key, "Value went down", statistic, new_value, prev_value]
                    #continue
                #ignored = False
                details[key][0] = new_value - prev_value
                prev_value = new_value
                new_statistic[loc][key] = details[key]
    return new_statistic

for d in statistics:
    statistics[d] = disaggregate(d, statistics[d])

# Write this out in Sahana CSV format
print "Writing out in Sahana format..."
import csv
import os
from urlparse import urlparse
from s3 import s3_unicode

new_file = open(OUTPUT_CSV, "wb")
new_csv = csv.writer(new_file, delimiter=",", quotechar='"')
# Header row
new_csv.writerow(["Statistic", "Value", "Country", "L1", "L2", "L3", "Date", "Source", "Source Organisation", "Source URL"])

split = os.path.split
def write_details_to_csv(csv_file, statistic, data):
    cnt = 0
    writerow = csv_file.writerow
    for (location, details) in data.items():
        loc = location_list[location]
        for key in sorted(details.keys()):
            row = details[key]
            source = row[2]
            source_url = ""
            url = urlparse(source)
            if url[0] != "":
                source_url = source
                (head, tail) = split(url[2])
                source = tail.replace("%20", " ")
            cnt += 1
            writerow([statistic, row[0], loc[0], loc[1], loc[2], loc[3], key, s3_unicode(source).encode("utf-8"), row[1], source_url])
            
for s in statistics:
    write_details_to_csv(new_csv, s, statistics[s])

new_file.close()

# @ToDo: Diff to just more recent data
# Open the existing prepop data file
# Find the last date that data was added to the prepop file
# Add recent data to the prepop file
# Save the prepop file

# Import the new data into the database
print "Importing data..."
auth.override = True
stylesheet = os.path.join(request.folder, "static", "formats", "s3csv", "disease", "stats_data.xsl")
resource = s3db.resource("disease_stats_data")
File = open(OUTPUT_CSV, "r")
resource.import_xml(File, format="csv", stylesheet=stylesheet)
db.commit()

if len(rejected_loc) or len(rejected_data) or len(suspect_data) or len(new_org):
    # Write out Error Log
    import codecs

    error_filename = "ebola_error_report_%s.txt" % todays_date
    error_file = codecs.open(error_filename, "wb", "utf-8")
    if len(rejected_loc):
        error_file.write("Rejected data because the location cannot be verified or covers multiple places (multiple places just delays the start date of the data)\r\n")
        error_file.write("===============================================================================\r\n")
        for (loc, details) in rejected_loc.items():
            error_file.write("location %s was rejected %s times\r\n" % (loc, details))
    if len(rejected_data):
        error_file.write("\r\nRejected Data\r\n")
        error_file.write("========================\r\n")
        for (loc, details) in rejected_data.items():
            error_file.write("data rejected because %s - (%s, %s, %s) new value: %s previous value: %s\r\n" % (details[1], loc, details[0], details[2], details[3], details[4]))
    if len(suspect_data):
        error_file.write("\r\nSuspect Data\r\n")
        error_file.write("========================\r\n")
        for (loc, details) in suspect_data.items():
            error_file.write("data suspect because %s - (%s, %s, %s) new value: %s previous value: %s\r\n" % (details[1], loc, details[0], details[2], details[3], details[4]))
    if len(new_org):
        error_file.write("\r\nSource Organisations which cannot be verified\r\n")
        error_file.write("===============================================================================\r\n")
        for (org, details) in new_org.items():
            error_file.write("organisation %s was seen %s times\r\n" % (org, details))

    print "See Error Log for issues: cat %s" % error_filename
