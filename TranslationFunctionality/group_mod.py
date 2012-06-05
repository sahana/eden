#!/usr/bin/python
import sys
import os
import getStrings
d = {}
vflag=0
rest_dirs = []

def init():

      global d,rest_dirs

      mod = get_module_list()

      for m in mod:
	   d[m] = []
      d["core"] = []
      d["special"] = []

      rest_dirs = ["languages","deployment-templates","docs","tests","test", ".git", "TranslationFunctionality"]

      group_files("../","core")


def get_module_list():
   
   mod = []

   cont_dir = os.path.abspath("../controllers")
   mod_files = os.listdir(cont_dir)

   for f in mod_files:
      cur_file = os.path.join(cont_dir,f)
      mod.append(f[:-3])

   return mod

def group_files(currentDir,curmod):
      
      global d, vflag

      currentDir = os.path.abspath(currentDir)
      base_dir = os.path.basename(currentDir)

      if base_dir in rest_dirs:
             return

      if base_dir == "views":
            vflag=1
      

      files = os.listdir(currentDir)
      
      for f in files:
          curFile = os.path.join(currentDir,f)
	  if os.path.isdir(curFile):

		  if base_dir=="views":
		         group_files(curFile,os.path.basename(curFile))
		  else:
                         group_files(curFile,curmod)
	  else:
		  if vflag==1:
		     base = curmod
		  elif curFile.endswith("/eden/modules/eden/menus.py") or curFile.endswith("/eden/modules/s3cfg.py"):
                     base = "special"
		  else:
		     base = os.path.splitext(f)[0]
                     if base_dir == "s3" and "s3" in base:
		       base = base[2:]
		     elif base_dir == "models" and "_" in base:
		       base = base.split('_')[1]

		  if base in d.keys():
		     d[base].append(curFile)
		  else:
		     d["core"].append(curFile)
     


      if base_dir == "views":
           vflag=0


def get_files_by_module(module):
        
	if module in d.keys():
             return d[module]
	else:
             print "Module '%s' doesn't exist!" %module
	     return []



def get_strings_by_module(module):
        
	if module in d.keys():
	     fileList = d[module]
	else:
             print "Module '%s' doesn't exist!" %module
	     return []

        strings = []

	for f in fileList:
	     if f.endswith(".py") == True:
                  strings.append( ("File:",f) )
	          strings += getStrings.findstr(f,"ALL",get_module_list())
	
	fileList = d["special"]	  
        for f in fileList:
	     if f.endswith(".py") == True:
                  strings.append( ("File:",f) )
	          strings += getStrings.findstr(f,module,get_module_list())

	return strings



def get_strings_by_file(filename):
	
	if os.path.isfile(filename):
	   filename = os.path.abspath(filename)
	else:
	   print  "'%s' is not a valid file path!"%filename
           return []

	if filename.endswith(".py") == True:
	         return getStrings.findstr(filename, "ALL", get_module_list())
	else:
	        print "Please enter a '.py' file path"
		return []


def _main():

      if len(sys.argv) > 1:

	   if sys.argv[1] == "-gml":
	      l = get_module_list()
	      for m in l:
	         print m

	     
	   elif sys.argv[1] == "-gfm":
	     init()
	     it = 2
	     while it < len(sys.argv):
                 files = get_files_by_module(sys.argv[it])

		 if len(files) != 0:
		    print "Module : " + sys.argv[it]
		    for f in files:
			  print f
		 print
		 it += 1

            
           elif sys.argv[1] == "-gsf":
	       it=2
	       while it < len(sys.argv):
		       strings = get_strings_by_file(sys.argv[it])
		       print "File : " + sys.argv[it]
		       for (l,s) in strings:
		          print l,s

		       it += 1
          
	   elif sys.argv[1] == "-gsm":
                init()
	        it=2
		while it < len(sys.argv):
			strings = get_strings_by_module(sys.argv[it])
                        print "Module : " + sys.argv[it]
			for (l,s) in strings:
				print l,s

		        it += 1

	   else:
		print "Please enter a valid option."




if __name__ == '__main__':
   _main()
