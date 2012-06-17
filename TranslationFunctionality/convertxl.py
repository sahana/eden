#!/usr/bin/python
import sys
import xlwt
import group_mod



def remove_quotes(Strings):

	l = []

	for (loc,data) in Strings:
            if data[0] == '"' and data[-1] == '"' or data[0] == "'" and data[-1] == "'":
	            data = data[1:-1]
            l.append( (loc,data) )

        return l


def remove_duplicates(Strings):
     
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

    l.sort( key=lambda tup: tup[1] )
    
    return l
     

def create_spreadsheet(Strings):

        wbk = xlwt.Workbook()
        sheet = wbk.add_sheet('Translate')
        style = xlwt.XFStyle()
        font = xlwt.Font()
        font.name = 'Times New Roman'
	style.font = font
	
	sheet.write(0,0,'location',style)
	sheet.write(0,1,'source',style)
	sheet.write(0,2,'target',style)

	row_num = 1

	for (loc,data) in Strings:
	    sheet.write(row_num,0,loc,style)
            sheet.write(row_num,1,data,style)
	    sheet.write(row_num,2,'',style)
	    row_num+=1

	for colx in range(0,3):
            sheet.col(colx).width = 14000

        wbk.save('trans.xls')




def convert_to_xls(modlist,filelist):

	group_mod.init()

	Strings = []

	for mod in modlist:
	     Strings += group_mod.get_strings_by_module(mod)
        
	for f in filelist:
	     Strings += group_mod.get_strings_by_file(f)
        
        Strings = remove_quotes(Strings)
       
        Strings = remove_duplicates(Strings)

        create_spreadsheet(Strings)

 

def main():
        
	mflag = 0
	fflag = 0
	modlist = []
	filelist = []

	for i in range(1,len(sys.argv)):
            
		if sys.argv[i] == "-gsm":
		    mflag = 1
		    fflag = 0

		elif sys.argv[i] == "-gsf":
		    fflag = 1
		    mflag = 0

		elif mflag == 1:
		    modlist.append(sys.argv[i])

	        elif fflag == 1:
		   filelist.append(sys.argv[i])
	   
        convert_to_xls(modlist,filelist)  

	sys.exit(0)

        


if __name__=='__main__':
   main()
