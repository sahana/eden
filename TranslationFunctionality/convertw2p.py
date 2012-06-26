#!/usr/bin/python

import os
import sys
import parsew2p
import parsecsv
from subprocess import call


def convert_to_w2p( csvfiles, w2pfilename, option):
      
	""" Function to merge multiple translated csv files into one
	    and then merge/overwrite the existing w2p language file """ 

        # Dictionary to store (location,translated string) with untranslated string as the key	
	d = {}

	for f in csvfiles:
	      data = parsecsv.read_csvfile(f)
              for row in data:
	          if row[1] in d.keys():
                      if d[row[1]][1] == '':
		          d[row[1]] = (row[0],row[2])
                  else: 
			  d[row[1]] = (row[0],row[2])
        
	# If strings are to be merged with existing .py file
        if option == '-m':
              data = parsew2p.read_w2pfile(w2pfilename)
              for row in data:
	          tmprow = ( row[0][1:-1], row[1][1:-1] )
                  row = ( tmprow[0], tmprow[1].decode('string-escape') )
	          if row[0] not in d.keys():
                     d[row[0]] = ('',row[1])


        # Created a list of sorted tuples (location,original string,translated string) 
        data = []
	for k in sorted(d.keys()):
		data.append( [ d[k][0] , k ,d[k][1] ])

        # Create intermediate csv file
	csvfilename = w2pfilename[:-2] + "csv"
        parsecsv.write_csvfile( csvfilename , data)

        # Convert the csv file to intermediate po file
	pofilename = w2pfilename[:-2] + "po"
	call(["csv2po","-i",csvfilename,"-o",pofilename])

        # Convert the po file to w2p language file
	call(["po2web2py","-i",pofilename,"-o",w2pfilename])

        # Remove intermediate files
#	os.unlink(pofilename)
#	os.unlink(csvfilename)

#------------------------------------------------------------------------------------------------


def main():

	""" Main to process command line arguments """

	csvfiles = []

        # Option for merge or overwrite
	option = sys.argv[1]
	w2pfilename = sys.argv[2]

        # Creating list of translated csv files
        for i in range(3,len(sys.argv)):
		csvfiles.append(sys.argv[i])

        convert_to_w2p(csvfiles,w2pfilename,option)


if __name__=='__main__':
   main()

#END===============================================================================================

