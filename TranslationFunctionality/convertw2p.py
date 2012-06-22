#!/usr/bin/python

import sys
import parsew2p
import parsecsv
from subprocess import call




def convert_to_w2p( csvfiles, w2pfilename, option):

	d = {}

	for f in csvfiles:
	      data = parsecsv.read_csvfile(f)
              for row in data:
	          if row[1] in d.keys():
                      if d[row[1]][1] == '':
		          d[row[1]] = (row[0],row[2])
                  else: 
			  d[row[1]] = (row[0],row[2])

        if option == '-m':
              data = parsew2p.read_w2pfile(w2pfilename)
              for row in data:
	          row = ( row[0][1:-1], row[1][1:-1] )
	          if row[0] not in d.keys():
                     d[row[0]] = ('',row[1])

        data = []
	for k in sorted(d.keys()):
		data.append( [ d[k][0] , k ,d[k][1] ])

	csvfilename = w2pfilename[:-2] + "csv"
        parsecsv.write_csvfile( csvfilename , data)

	pofilename = w2pfilename[:-2] + "po"
	call(["csv2po","-i",csvfilename,"-o",pofilename])

	call(["po2web2py","-i",pofilename,"-o",w2pfilename])

	call(["rm",pofilename,csvfilename])




def main():

	csvfiles = []
	option = sys.argv[1]
	w2pfilename = sys.argv[2]

        for i in range(3,len(sys.argv)):
		csvfiles.append(sys.argv[i])

        convert_to_w2p(csvfiles,w2pfilename,option)


if __name__=='__main__':
   main()

