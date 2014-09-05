#!/bin/env python

# Generate a CSV of names suitable for import into Eden
#  via tasks.cfg:
# hrm,person,people.csv,person.xsl
#  or via w2p:
# auth.override = True
# resource = s3db.resource("pr_person")
# stylesheet = os.path.join(request.folder, "static", "formats", "s3csv", "hrm", "person.xsl")
# filename = "people.csv"
# File = open(filename, "r")
# resource.import_xml(File, format="csv", stylesheet=stylesheet)
# db.commit()
#
# @ToDo: Email Addresses, Job Titles
# @ToDo: Localised names (names uses US Census data as source)
#

type = "Volunteer"
number = 1900
organisation = "Philippine Red Cross"
# Lookup file needs to have Country/L0 and as far down L1, L2, L3, L4 as you wish...in order
lookup = "PH_L4.csv"

import codecs
import csv
csv.field_size_limit(1000000000)

#lookupFile = open(lookup, "r")
# If BOM present, need this:
lookupFile = codecs.open(lookup, "rU", encoding="utf-8-sig")

def unicode_csv_reader(utf8_data, dialect=csv.excel):
    csv_reader = csv.reader(utf_8_encoder(utf8_data), dialect)
    for row in csv_reader:
        yield [unicode(cell, "utf-8") for cell in row]

def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode("utf-8")

#reader = csv.reader(lookupFile)
reader = unicode_csv_reader(lookupFile)
header = reader.next()
numcols = len(header)
max_level = None
for i in range(0, numcols):
    col = header[i]
    if col in ("Country", "L0"):
        max_level = 0
    elif col == "L1":
        max_level = 1
    elif col == "L2":
        max_level = 2
    elif col == "L3":
        max_level = 3
    elif col == "L4":
        max_level = 4

locations = []
lappend = locations.append
for row in reader:
    country = L1 = L2 = L3 = L4 = ""
    for i in range(0, numcols):
        col = header[i]
        if col in ("Country", "L0"):
            country = row[i]
            if max_level == 0:
                lappend((country,))
        elif col == "L1":
            L1 = row[i]
            if max_level == 1:
                lappend((country, L1))
        elif col == "L2":
            L2 = row[i]
            if max_level == 2:
                lappend((country, L1, L2))
        elif col == "L3":
            L3 = row[i]
            if max_level == 3:
                lappend((country, L1, L2, L3))
        elif col == "L4":
            L4 = row[i]
            if max_level == 4:
                lappend((country, L1, L2, L3, L4))

lookupFile.close()
locations_len = len(locations)

from names import get_full_name
from random import randrange

output = "people.csv"
outputFile = open(output, "w")
writer = csv.writer(outputFile)

# Header
writer.writerow(["Sex","First Name","Last Name","Type","Organisation","Home Country","Home L1","Home L2","Home L3","Home L4"])

country = L1 = L2 = L3 = L4 = ""
male = True
for i in xrange(number):
    j = randrange(0, locations_len - 1)
    location = locations[j]
    country = location[0].encode("utf-8")
    if max_level > 0:
        L1 = location[1].encode("utf-8")
    if max_level > 1:
        L2 = location[2].encode("utf-8")
    if max_level > 2:
        L3 = location[3].encode("utf-8")
    if max_level > 3:
        L4 = location[4].encode("utf-8")
    if male:
        name = get_full_name(gender="male")
        parts = name.split(" ", 1)
        writer.writerow(["Mr.",parts[0], parts[1], type, organisation, country, L1, L2, L3, L4])
        male = False
    else:
        name = get_full_name(gender="female")
        parts = name.split(" ", 1)
        writer.writerow(["Ms.",parts[0], parts[1], type, organisation, country, L1, L2, L3, L4])
        male = True

outputFile.close()
