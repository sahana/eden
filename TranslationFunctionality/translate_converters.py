#!/usr/bin/python

import os
import sys
import csv
import xlwt
import translate_file_management
from subprocess import call

class StringsToExcel:

	"""Class to convert strings to .xls format"""

        def remove_quotes(self,Strings):

	   """ Function to remove single or double quotes surrounding the strings """

	   l = []

	   for (d1,d2) in Strings:
               if d1[0] == '"' and d1[-1] == '"' or d1[0] == "'" and d1[-1] == "'":
	               d1 = d1[1:-1]
               if d2[0] == '"' and d2[-1] == '"' or d2[0] == "'" and d2[-1] == "'":
	               d2 = d2[1:-1]
               l.append( (d1,d2) )

           return l

        #----------------------------------------------------------------------------
 
        def remove_duplicates(self,Strings):

           """ Function to club all the duplicate strings into one row with ';' separated locations """
     
           uniq = {}

           for (loc,data) in Strings:
                uniq[data] = ''

           for (loc,data) in Strings:

                if uniq[data] != '':
                   uniq[data] = uniq[data] + ';' + loc
                else:
	           uniq[data] = loc
    
           l=[]

           for data in uniq.keys():
               l.append( (uniq[data],data) )

    
           return l

        #---------------------------------------------------------------------------------

        def create_spreadsheet(self,Strings):

	    """ Function to create a spreadsheet (.xls file) of strings with
	        location, original string and translated string as columns """

            # Defining spreadsheet properties
            wbk = xlwt.Workbook("utf-8")
            sheet = wbk.add_sheet('Translate')
            style = xlwt.XFStyle()
            font = xlwt.Font()
            font.name = 'Times New Roman'
	    style.font = font
	
	    sheet.write(0,0,'location',style)
	    sheet.write(0,1,'source',style)
	    sheet.write(0,2,'target',style)

	    row_num = 1

            # Writing the data to spreadsheet
	    for (loc,d1,d2) in Strings:
               d2 = d2.decode('string-escape').decode("utf-8")
	       sheet.write(row_num,0,loc,style)
               sheet.write(row_num,1,d1,style)
               sheet.write(row_num,2,d2,style)
	       row_num+=1

	    # Setting column width
	    for colx in range(0,3):
                sheet.col(colx).width = 15000

            # Saving the spreadsheet    
            wbk.save('trans.xls')

        #----------------------------------------------------------------------------------

        def convert_to_xls(self,langfile,modlist,filelist):

	    """ Function to get the strings by module(s)/file(s), merge with those strings
	        from existing w2p language file which are already translated and call the
	        'create_spreadsheet()' method """


	    NewStrings = []
            A = translate_file_management.TranslateAPI()
            R = translate_file_management.TranslateReadFiles()

            # Retrieve strings for a module
	    for mod in modlist:
	         NewStrings += A.get_strings_by_module(mod)

            # Retrieve strings in a file
	    for f in filelist:
	         NewStrings += A.get_strings_by_file(f)
        
            NewStrings = self.remove_quotes(NewStrings)
            NewStrings = self.remove_duplicates(NewStrings)
            NewStrings.sort( key=lambda tup: tup[1] )

            # Retrive strings from existing w2p language file
	    OldStrings = R.read_w2pfile(langfile)
            OldStrings = self.remove_quotes(OldStrings)
	    OldStrings.sort( key=lambda tup: tup[0] )


            # Merging those strings which were already translated earlier

	    Strings = []

	    i = 0
	    lim = len(OldStrings)

	    for (l,s) in NewStrings:

	          while i<lim and OldStrings[i][0] < s:
	              i+=1
                 
	          if i!=lim and OldStrings[i][0] == s and OldStrings[i][1].startswith("*** ") == False:
	              Strings.append( (l,s,OldStrings[i][1]) )
	          else:
	              Strings.append( (l,s,'') )

            self.create_spreadsheet(Strings)


#==================================================================================================


class CsvToWeb2py:

	""" Class to convert a group of csv files to a web2py language file"""

        def write_csvfile(self,fileName, data):

	   """ Function to write a list of rows into a csv file """
	 
           # Quoting all the elements while writing
	   transWriter = csv.writer(open(fileName, 'wb'), delimiter=' ', quotechar='"', quoting = csv.QUOTE_ALL)
	   transWriter.writerow(["location","source","target"])
	   for row in data:
	      transWriter.writerow(row)    
        
        #---------------------------------------------------------------------------------------------------

        
        def convert_to_w2p( self, csvfiles, w2pfilename, option):
      
	   """ Function to merge multiple translated csv files into one
	       and then merge/overwrite the existing w2p language file """ 

           # Dictionary to store (location,translated string) with untranslated string as the key	
	   d = {}
           R = translate_file_management.TranslateReadFiles()         

	   for f in csvfiles:
	         data = R.read_csvfile(f)
                 for row in data:
	             if row[1] in d.keys():
                         if d[row[1]][1] == '':
		             d[row[1]] = (row[0],row[2])
                     else: 
			     d[row[1]] = (row[0],row[2])
        
           # If strings are to be merged with existing .py file
           if option == '-m':
                 data = R.read_w2pfile(w2pfilename)
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
           self.write_csvfile( csvfilename , data)

           # Convert the csv file to intermediate po file
	   pofilename = w2pfilename[:-2] + "po"
	   call(["csv2po","-i",csvfilename,"-o",pofilename])

           # Convert the po file to w2p language file
	   call(["po2web2py","-i",pofilename,"-o",w2pfilename])

           # Remove intermediate files
	   os.unlink(pofilename)
	   os.unlink(csvfilename)   
      
        #----------------------------------------------------------------------------- 

#END=================================================================================================
