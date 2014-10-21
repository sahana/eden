#!/usr/bin/python

# This script will update the ebola.cases data file for prepop

# Needs to be run in the web2py environment
# cd web2py
# python web2py.py -S eden -M -R applications/eden/static/scripts/tools/ebola.cases.update.py

import xlrd
import urllib2
import string

# Open the file from the remote server
# @todo write the remote file to a temp file and then pass to load_workbook  
remote_file_name = "https://rowca.egnyte.com/dd/mfIyWzxlh7"
u = urllib2.urlopen(remote_file_name)
local_file_name = "/home/graeme/Downloads/Data Ebola (Public).xlsx"

wb = xlrd.open_workbook(file_contents=u.read())
ws = wb.sheet_by_name('ROWCA Ebola All Sec Review')

rejected_loc={}
rejected_data={}

def lookup_loc(location, country):
    # If the location ends with "County", then strip it out and try again
    if location[-6:] == "County":
        return get_loc_from_db(location[:-6].strip(), country)
    if location == "Western Area":
        return get_loc_from_db("Western", country)
    if location.startswith("Western Area"):
        return get_loc_from_db(location[12:].strip(), country)
    if location in rejected_loc:
        rejected_loc[location] += 1
    else:
        rejected_loc[location] = 1
    return None

def get_loc_from_db(location, country):
    db = current.db
    table = s3db.gis_location
    query = (table.name == location)
    location_row = db(query).select(limitby=(0, 1)).first()
    if location_row == None:
        return lookup_loc(location, country)
    level = location_row.level
    L3 =  location_row.L3
    L2 =  location_row.L2
    L1 =  location_row.L1
    # @todo: Grab these codes from the database rather than hard code
    if country == "Sierra Leone":
        country_code =  "SL"
    elif country == "Liberia":
        country_code =  "LR"
    elif country == "Guinea":
        country_code =  "GN"
    elif country == "Nigeria":
        country_code =  "NG"
    elif country == "Senegal":
        country_code =  "SN"
    return (country_code, L1, L2, L3)

def store_details(location, row):
    demographic = row[2].strip()
    value = row[3]
    date_t = xlrd.xldate_as_tuple(row[4],0)
    date = "%s/%s/%s" % (date_t[0], date_t[1], date_t[2])  
    source = row[5].strip()
    if row[6] != None:
        source_url = row[6].strip()
    else:
        source_url = "" 

    if demographic == "Cases":
        d_cases[location][date] = [demographic, value, source, source_url]
    elif demographic == "Confirmed cases":
        d_ccases[location][date] = [demographic, value, source, source_url]
    elif demographic == "Deaths":
        d_deaths[location][date] = [demographic, value, source, source_url]
    elif demographic == "New cases":
        d_other[location][date] = [demographic, value, source, source_url]
    elif demographic == "Probable cases":
        d_other[location][date] = [demographic, value, source, source_url]
    elif demographic == "Suspected cases":
        d_other[location][date] = [demographic, value, source, source_url]

def extractRow(row):
    country = row[0].strip()
    location = row[1].strip()
    # Ignore combined locations
    if location == "National" or ' and ' in location:
        if location in rejected_loc:
            rejected_loc[location] += 1
        else:
            rejected_loc[location] = 1
        return
    if not location in location_list:
        # Ensure some standard Capitalisation - or at least try ;)
        location = string.capwords(location) 
        loc_row = get_loc_from_db(location, country)
        location_list[location] = loc_row
        d_cases[location] = {}
        d_ccases[location] = {}
        d_deaths[location] = {}
        d_other[location] = {}

    if location_list[location] != None:
        # Now we have verified location data, add the details
        store_details(location, row)
    return        


# Now extract the data
location_list = {}
d_cases = {}
d_ccases = {}
d_deaths = {}
d_other = {}

for rcnt in xrange(1,ws.nrows):
    row = ws.row_values(rcnt,0,7)
    extractRow(row)

# Dis-aggregate the running total for cases, confirmed cases and deaths
def disaggregate(demographic):
    ignored = False
    new_demographic = {}
    for (loc, details) in demographic.items():
        new_demographic[loc] = {}
        prev_value = 0
        for key in sorted(details.keys()):
            new_value = details[key][1]
            try:
                if prev_value != new_value:
                    if new_value == None:
                        rejected_data[loc]=[key, "None value", details[key][0], new_value, prev_value]
                        continue
                    if (new_value < prev_value) and not ignored:
                        # ignore the data value - but never ignore consecutive cases
                        ignored = True
                        rejected_data[loc]=[key, "Ignored record", details[key][0], new_value, prev_value]
                        continue
                    ignored = False
                    details[key][1] = new_value - prev_value
                    prev_value = new_value
                    new_demographic[loc][key] = details[key]
            except TypeError:
                rejected_data[loc]=[key, "Erroneous record", details[key][0], new_value, prev_value]
                pass
    return new_demographic

d_cases = disaggregate(d_cases)
d_ccases = disaggregate(d_ccases)
d_deaths = disaggregate(d_deaths)

# Write this out to a prepop file
import csv
from time import gmtime, strftime
from urlparse import urlparse
import os
todays_date = strftime("%Y-%m-%d", gmtime())
new_prepop_filename = "ebola_prepop_%s.csv" % todays_date
new_file = open(new_prepop_filename, 'wb')
new_csv = csv.writer(new_file, delimiter=',', quotechar='"')
new_csv.writerow(["Demographic", "Value", "Country", "L1", "L2", "L3", "Date", "Source", "Source Organisation", "Source URL"])

def write_details_to_csv (csv_file, detail_list):
    cnt = 0
    for (loc,details) in detail_list.items():
        location = location_list[loc]
        for key in sorted(details.keys()):
            row = details[key]
            source = row[3]
            source_url = ""
            url = urlparse(source)
            if url[0] != "":
                source_url = source
                (head, tail) = os.path.split(url[2])
                source = tail
            cnt = cnt +1
            csv_file.writerow([row[0], row[1], location[0], location[1], location[2], location[3], key, source, row[2], source_url])

write_details_to_csv(new_csv, d_cases)
write_details_to_csv(new_csv, d_ccases)
write_details_to_csv(new_csv, d_deaths)
write_details_to_csv(new_csv, d_other)

# Open the existing prepop data file

# Find the last date that data was added to the prepop file

# Add recent data to the prepop file

# Save the prepop file

# Add the new data to the database

error_filename = "ebola_error_report_%s.txt" % todays_date
error_file = open(error_filename, 'wb')
error_file.write("Rejected data because the location cannot be verified or covers multiple places\r\n")
error_file.write("===============================================================================\r\n")
for (loc, details) in rejected_loc.items():
    error_file.write("location %s was rejected %s times\r\n" % (loc, details))
error_file.write("\r\nData ignored or in error\r\n")
error_file.write("========================\r\n")
for (loc, details) in rejected_data.items():
    if details[1] != "None value":
        error_file.write("data was rejected because %s - (%s, %s, %s) new value: %s previous value: %s\r\n" % (details[1], loc, details[0], details[2], details[3], details[4]))
for (loc, details) in rejected_data.items():
    if details[1] == "None value":
        error_file.write("data was rejected because %s - (%s, %s, %s) new value: %s previous value: %s\r\n" % (details[1], loc, details[0], details[2], details[3], details[4]))
