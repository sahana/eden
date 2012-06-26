#!/usr/bin/python
import sys
import xlwt
import group_mod
import parsew2p



def remove_quotes(Strings):

	""" Function to remove single or double quotes surrounding the strings """

	l = []

	for (d1,d2) in Strings:
            if d1[0] == '"' and d1[-1] == '"' or d1[0] == "'" and d1[-1] == "'":
	            d1 = d1[1:-1]
            if d2[0] == '"' and d2[-1] == '"' or d2[0] == "'" and d2[-1] == "'":
	            d2 = d2[1:-1]
            l.append( (d1,d2) )

        return l

#-----------------------------------------------------------------------------------------------	

def remove_duplicates(Strings):

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

#---------------------------------------------------------------------------------------------------

def create_spreadsheet(Strings):

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

#----------------------------------------------------------------------------------------


def convert_to_xls(langfile,modlist,filelist):

	""" Function to get the strings by module(s)/file(s), merge with those strings
	    from existing w2p language file which are already translated and call the
	    'create_spreadsheet()' method """


	group_mod.init()

	NewStrings = []

        # Retrieve strings for a module
	for mod in modlist:
	     NewStrings += group_mod.get_strings_by_module(mod)

        # Retrieve strings in a file
	for f in filelist:
	     NewStrings += group_mod.get_strings_by_file(f)
        
        NewStrings = remove_quotes(NewStrings)
        NewStrings = remove_duplicates(NewStrings)
        NewStrings.sort( key=lambda tup: tup[1] )

        # Retrive strings from existing w2p language file
	OldStrings = parsew2p.read_w2pfile(langfile)
        OldStrings = remove_quotes(OldStrings)
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

        create_spreadsheet(Strings)

#-------------------------------------------------------------------------------------------------------

def main():
        
	""" Main to process command line arguments """

	mflag = 0
	fflag = 0
	modlist = []
	filelist = []

        # w2p language file
        langfile = sys.argv[1]

	for i in range(2,len(sys.argv)):
            
		if sys.argv[i] == "-gsm":
		    mflag = 1
		    fflag = 0

		elif sys.argv[i] == "-gsf":
		    fflag = 1
		    mflag = 0

                # appending to list of modules
		elif mflag == 1:
		    modlist.append(sys.argv[i])
                
	        # appending to list of files
	        elif fflag == 1:
		    filelist.append(sys.argv[i])
	   
        convert_to_xls(langfile,modlist,filelist)  

	sys.exit(0)        


if __name__=='__main__':
   main()

#END=============================================================================	
