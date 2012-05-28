#!/usr/bin/python
import sys
import os

mod = []

def get_module_list():
   
   global mod
   cont_dir = os.path.abspath("../controllers")
   mod_files = os.listdir(cont_dir)
   for f in mod_files:
      cur_file = os.path.join(cont_dir,f)
      mod.append(f[:-3])
 
def _main():
      get_module_list()

if __name__ == '__main__':
   _main()
