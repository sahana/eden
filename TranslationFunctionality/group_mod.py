#!/usr/bin/python
import sys
import os
import getStrings
d = {}
rest_dirs = []

def init(): 
      
      """ Set up dictionary containing files on a module by module basis """ 	
	
      global d,rest_dirs

      mod = get_module_list()

      for m in mod:
	   d[m] = []
	
      # List of files belonging to 'core' module	   
      d["core"] = []  

      # List of 'special' files which contains strings from more than one module
      d["special"] = []   

      # Directories which are not required to be searched
      rest_dirs = ["languages","deployment-templates","docs","tests","test", ".git", "TranslationFunctionality"]
      
      #Calls the function to group the files
      group_files("../",'',0)

#----------------------------------------------------------------------------------------------------------------

def get_module_list():
   
   """ Returns a list of modules using files in /eden/controllers/ as point of reference """	
   mod = []

   cont_dir = os.path.abspath("../controllers")
   mod_files = os.listdir(cont_dir)

   for f in mod_files:
      cur_file = os.path.join(cont_dir,f)
      mod.append(f[:-3])

   return mod

#----------------------------------------------------------------------------------------------------------------

def group_files(currentDir,curmod, vflag):

      """ Recursive function to group the Eden files into respective modules """

      global d

      currentDir = os.path.abspath(currentDir)
      base_dir = os.path.basename(currentDir)

      if base_dir in rest_dirs:    
             return

      # If current directory is '/eden/views', set vflag
      if base_dir == "views":            
            vflag=1
      

      files = os.listdir(currentDir)
      
      for f in files:
          curFile = os.path.join(currentDir,f)
	  if os.path.isdir(curFile):

                  # If the current directory is /eden/views, categorize files based on the directory name
		  if base_dir=="views":
		         group_files(curFile,os.path.basename(curFile),vflag)
		  else:
                         group_files(curFile,curmod,vflag)
	  else:
	          # If inside /eden/views, use parent directory name for categorization
		  if vflag==1:          
		     base = curmod

                  # Categorize file as "special" as it contains strings belonging to various modules
		  elif curFile.endswith("/eden/modules/eden/menus.py") or curFile.endswith("/eden/modules/s3cfg.py") or curFile.endswith("/eden/models/000_config.py"):
                     base = "special"
		  else:
                     # Removing '.py'
		     base = os.path.splitext(f)[0]   
		     
		     # If file is inside /eden/modules/s3 directory and it contains "s3" as a prefix, remove that prefix to get the module name
                     if base_dir == "s3" and "s3" in base:
		       base = base[2:]

		     # If file is inside /eden/models and file is of the type var_module.py, remove the "var_" prefix
		     elif base_dir == "models" and "_" in base:
		       base = base.split('_')[1]
                  
		  # If base refers to a module, append to corresponding list
		  if base in d.keys():               
		     d[base].append(curFile)
		  else:
                     # else append it to "core" files list
		     d["core"].append(curFile)       
     

#-----------------------------------------------------------------------------------------------------------------------------

def get_files_by_module(module):

	""" Return a list of files corresponding to an input module """
        
	if module in d.keys():
             return d[module]
	else:
             print "Module '%s' doesn't exist!" %module
	     return []

#------------------------------------------------------------------------------------------------------------------------------

def get_strings_by_module(module):

	""" Return a list of strings corresponding to an input module """
        
	if module in d.keys():
	     fileList = d[module]
	else:
             print "Module '%s' doesn't exist!" %module
	     return []

        strings = []
	tmpstr = []

	for f in fileList:
	     if f.endswith(".py") == True:
	          tmpstr = getStrings.findstr(f,"ALL",get_module_list())
		  for s in tmpstr:
		      strings.append( ( f+":"+str(s[0]) , s[1]) ) 
		      

	
        # Handling "special" files separately
	fileList = d["special"]	  
        for f in fileList:
	     if f.endswith(".py") == True:
                  tmpstr = getStrings.findstr(f,module,get_module_list())
	          for s in tmpstr:
		      strings.append( (f+":"+str(s[0]), s[1]) )

	return strings

#---------------------------------------------------------------------------------------------------------------------------------

def get_strings_by_file(filename):

	""" Return a list of strings in a given file """
	
	if os.path.isfile(filename):
	   filename = os.path.abspath(filename)
	else:
	   print  "'%s' is not a valid file path!"%filename
           return []

	if filename.endswith(".py") == True:
	         strings = []
	         tmpstr = getStrings.findstr(filename, "ALL", get_module_list())
		 for s in tmpstr:
		    strings.append( (filename+":"+str(s[0]), s[1]) )
		 return strings
	else:
	        print "Please enter a '.py' file path"
		return []

#------------------------------------------------------------------------------------------------------------------------------------

def _main():

      """ Execution by command line options """

      if len(sys.argv) > 1:

	   if sys.argv[1] == "-gml":      # Get list of modules
	      l = get_module_list()
	      for m in l:
	         print m

	     
	   elif sys.argv[1] == "-gfm":    # Get list of files for a given module(s)
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

            
           elif sys.argv[1] == "-gsf":    # Get list of strings for a given file(s)
	       it=2
	       while it < len(sys.argv):
		       strings = get_strings_by_file(sys.argv[it])
		       print "File : " + sys.argv[it]
		       for (l,s) in strings:
		          print l,s

		       it += 1
          
	   elif sys.argv[1] == "-gsm":    # Get list of strings for a given module(s)
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

#END============================================================================================================
