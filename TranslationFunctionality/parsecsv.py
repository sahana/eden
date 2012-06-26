import csv

def read_csvfile(fileName):
       
	""" Function to read a csv file and return a list of rows """

        data = []	
        transReader = csv.reader(open(fileName, 'rb'))
	for row in transReader:
	    data.append(row)
	return data

#-------------------------------------------------------------------------

def write_csvfile(fileName, data):

	""" Function to write a list of rows into a csv file """
	
        # Quoting all the elements while writing
	transWriter = csv.writer(open(fileName, 'wb'), delimiter=' ', quotechar='"', quoting = csv.QUOTE_ALL)
	transWriter.writerow(["location","source","target"])
	for row in data:
	   transWriter.writerow(row)

#END=======================================================================
