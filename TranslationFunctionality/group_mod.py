#!/usr/bin/python
import sys
import os
import getStrings
mod = []
d = {}
vflag=0


def get_module_list():
   
   global mod
   cont_dir = os.path.abspath("../controllers")
   mod_files = os.listdir(cont_dir)
   for f in mod_files:
      cur_file = os.path.join(cont_dir,f)
      mod.append(f[:-3])

def group_files(currentDir,curmod):
      
      global d, vflag

      currentDir = os.path.abspath(currentDir)
      base_dir = os.path.basename(currentDir)

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
		  else:
		     base = os.path.splitext(f)[0]

		  if base_dir=="s3":
		      base = base[2:]	     

		  if base in mod:
		     d[base].append(curFile)
		  else:
		     d["core"].append(curFile)
     


      if base_dir == "views":
           vflag=0



def _main():

      get_module_list()

      for m in mod:
	      d[m] = []
      d["core"]=[]

      group_files("../","core")
      for m in d.keys():
	     print "\n"
	     print "Module:",m
	     for f in d[m]:
	         if f.endswith(".py") == True:
	                getStrings.findstr(f)


if __name__ == '__main__':
   _main()
