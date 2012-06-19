import csv

def read_csvfile(fileName):
       
        data = []	
        transReader = csv.reader(open(fileName, 'rb'))
	for row in transReader:
	    data.append(row)
	return data


def write_csvfile(fileName, data):

	transWriter = csv.writer(open(fileName, 'wb'), delimiter=' ', quotechar='"', quoting = csv.QUOTE_ALL)
	for row in data:
	   transWriter.writerow(row)
	
