#!/usr/bin/env python
# -*- coding: utf-8 -*-
# read_dict and write_dict are borrowed from web2py
# by lifeeth
import csv, cStringIO,codecs

# Unicode csv reader - not used here
def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [unicode(cell, 'utf-8') for cell in row]

# Web2py functions
def read_dict(filename):
    fp = codecs.open(filename, 'r')
    lang_text = fp.read().replace('\r\n', '\n')
    fp.close()
    if not lang_text.strip():
        return {}
    return eval(lang_text)

def write_dict(filename, contents):
    fp = open(filename, 'w')
    fp.write('# coding: utf8\n{\n')
    for key in sorted(contents):
        fp.write('%s: %s,\n' % (repr(key), repr(contents[key])))
    fp.write('}\n')
    fp.close()


existing = read_dict("fr.py")
reader = unicode_csv_reader(open("fr.csv", "rb"))
# web2py does not seem to be opening the file in unicode :|
#reader = csv.reader(open("fr.csv", "rb"))
newinput = {}
untranslated = {}
unknown = 0
for row in reader:
            newinput[row[0]] = row[1]

# Read the existing dict and update the values with those from csv
for sen1,sen2 in existing.iteritems():
    try:
        newinput[sen1]
        existing[sen1] = newinput[sen1]
    except:
        unknown=unknown+1
        untranslated[sen1]=sen2
        pass

# Write out ones that dont have a corresponding entry in the csv
writer = csv.writer(open("untranslated.csv", "wb"),dialect='excel',quoting=csv.QUOTE_NONNUMERIC)

for k,w in untranslated.items():
    writer.writerow([k,w])

print "Translation statistics :"
print "Total strings in original translation file    = " + str(len(existing))
print "Total strings in CSV file                     = " + str(len(newinput))
print "Total strings in original file not in the csv = " + str(unknown)

# Write out the frnew.py dict
write_dict("frnew.py", existing)
