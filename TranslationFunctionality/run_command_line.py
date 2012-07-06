#!/usr/bin/python
import sys
import translate_file_management
import translate_converters

def main():
 
	A = translate_file_management.TranslateAPI()
	X = translate_converters.StringsToExcel()
        W = translate_converters.CsvToWeb2py()

	option = sys.argv[1]

	if option == '-gml':
	     for m in A.get_modules():
		     print m
        
	elif option == '-gsm':
	     modlist = sys.argv[2:]
	     for m in modlist:
	          print "MODULE :" , m
	          s=A.get_strings_by_module(m)
	          for (l,d) in s:
		      print l,d

	elif option == '-gsf':
	     flist = sys.argv[2:]
	     for f in flist:
	         print "FILE :", f
	         s = A.get_strings_by_file(f)
	         for (l,d) in s:
		      print d

        elif option == '-gfm':
	     modlist = sys.argv[2:]
	     for m in modlist:
	          print "MODULE :", m
	          l = A.get_files_by_module(m)
	          for f in l:
		     print f

        elif option == '-c2xl':
	     w2pf = sys.argv[2]
	     modlist = sys.argv[3:]
	     X.convert_to_xls(w2pf,modlist,[])

	elif option == '-c2w':
	     w2pf = sys.argv[2]
	     op = sys.argv[3]
	     csvfiles = sys.argv[4:]
	     W.convert_to_w2p(csvfiles,w2pf,op)

        sys.exit(0)

if __name__ == '__main__':
    main()
