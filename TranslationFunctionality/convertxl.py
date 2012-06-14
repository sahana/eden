#!/usr/bin/python
import xlwt
import group_mod

def remove_duplicates(Strings):
     
    uniq = {}


    for (loc,data) in Strings:
         uniq[data] = ''

    for (loc,data) in Strings:

         if uniq[data] != '':
            uniq[data] = uniq[data] + ',' + loc
         else:
	    uniq[data] = loc
    
    l=[]

    for data in uniq.keys():
        l.append( (uniq[data],data) )
    
    return l
     

def create_spreadsheet(Strings):


	Strings = remove_duplicates(Strings)

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



def main():
	group_mod.init()
	create_spreadsheet(group_mod.get_strings_by_module("inv"))

if __name__=='__main__':
   main()
