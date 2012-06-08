#!/usr/bin/python

import sys
import os
import parser
import symbol
import token

class ParseFiles:

        def __init__(self):

            self.cflag = 0
            self.fflag = 0
            self.sflag = 0
            self.tflag = 0
            self.mflag = 0
            self.bracket = 0
            self.outstr = ''
            self.class_name = ''
            self.func_name = ''
            self.mod_name = ''
            self.findent = -1

        def parseConfig(self,spmod,strings,entry,modlist):


            if isinstance(entry,list):
               id = entry[0]
	       value = entry[1]
               if isinstance(value,list):
		    for element in entry:
		        self.parseConfig(spmod,strings,element,modlist)
               else:
                  if self.fflag == 1 and token.tok_name[id] == "NAME":
                     self.func_name = value
                     self.fflag = 0

                  elif token.tok_name[id] == "NAME" and value == "deployment_settings":
                      self.fflag = 1

	          elif self.tflag == 0 and self.func_name == "modules" and token.tok_name[id] == "STRING":
                      if value[1:-1] in modlist:
	                 self.mod_name = value[1:-1]

                  elif token.tok_name[id] == "NAME" and value == "T":
                      self.sflag = 1

                  elif self.sflag == 1:
	             if token.tok_name[id] == "LPAR":
		        self.tflag=1
		        self.bracket=1
	             self.sflag=0

	          elif self.tflag == 1:
	               if token.tok_name[id] == "LPAR":
	                    self.bracket+=1
	                    if self.bracket>1:
	                       self.outstr += '('
	               elif token.tok_name[id] == "RPAR":
                            self.bracket-=1
	                    if self.bracket>0:
	                        self.outstr += ')'
	                    else:
		               if spmod == "core":
                                  if self.func_name != "modules" and self.func_name not in modlist:
	                            strings.append( (entry[2], self.outstr) )  
                               elif (self.func_name == "modules" and self.mod_name == spmod) or (self.func_name == spmod):
	                            strings.append( (entry[2], self.outstr) )
	                       self.outstr=''
	                       self.tflag=0
	               elif self.bracket>0:
	                   self.outstr += value
                


        def parseS3cfg(self,spmod,strings,entry,modlist):

             if isinstance(entry,list):
                id = entry[0]
                value = entry[1]
                if isinstance(value,list):
		    for element in entry:
		        self.parseS3cfg(spmod,strings,element,modlist)
                else:
                  if self.fflag == 1:
                      self.func_name = value
                      self.fflag = 0
	          elif token.tok_name[id] == "NAME" and value == "def":
                      self.fflag = 1
                  
                  elif token.tok_name[id] == "NAME" and value == "T":
                      self.sflag = 1

                  elif self.sflag == 1:
	             if token.tok_name[id] == "LPAR":
		        self.tflag=1
		        self.bracket=1
	             self.sflag=0

	          elif self.tflag == 1:
	               if token.tok_name[id] == "LPAR":
	                    self.bracket+=1
	                    if self.bracket>1:
	                       self.outstr += '('
	               elif token.tok_name[id] == "RPAR":
                            self.bracket-=1
	                    if self.bracket>0:
	                        self.outstr += ')'
	                    else:
		               if spmod == "core":
                                  if '_' not in self.func_name or self.func_name.split('_')[1] not in modlist:
	                            strings.append( (entry[2], self.outstr) )  
                               elif '_' in self.func_name and self.func_name.split('_')[1] == spmod:
	                            strings.append( (entry[2], self.outstr) )
	                       self.outstr=''
	                       self.tflag=0
	               elif self.bracket>0:
	                   self.outstr += value


        def parseMenu(self,spmod,strings,entry,level):


            if isinstance(entry,list):
                id = entry[0]
                value = entry[1]
                if isinstance(value,list):
                    for element in entry:
                        self.parseMenu(spmod,strings,element,level+1)
                else:
	            if self.cflag == 1:
	               self.class_name = value
	               self.cflag = 0

	            elif token.tok_name[id] == "NAME" and value == "class":
	               self.cflag = 1
	 
                    elif self.fflag == 1:
                       self.func_name = value
                       self.fflag=0

	            elif token.tok_name[id] == "NAME" and value == "def" and (self.findent == -1 or level == self.findent) :
                       if self.class_name == "S3OptionsMenu": 
		         self.findent = level
	                 self.fflag = 1
	               else:
	                 self.func_name = ''

	            elif token.tok_name[id] == "NAME" and value == "T":
	                 self.sflag = 1

	            elif self.sflag == 1:
	                if token.tok_name[id] == "LPAR":
		           self.tflag=1
		           self.bracket=1
	                self.sflag=0

	            elif self.tflag == 1:
	                 if token.tok_name[id] == "LPAR":
	                       self.bracket+=1
	                       if self.bracket>1:
	                           self.outstr += '('
	                 elif token.tok_name[id] == "RPAR":
                               self.bracket-=1
	                       if self.bracket>0:
	                            self.outstr += ')'
	                       else:
		                   if spmod == "core":
                                      if self.func_name == '':
	                                 strings.append( (entry[2], self.outstr) )  
                                   elif self.func_name == spmod:
	                                 strings.append( (entry[2], self.outstr) )
	                           self.outstr=''
	                           self.tflag=0
	                 elif self.bracket>0:
	                      self.outstr += value

                    else:
	               if token.tok_name[id] == "NAME" and value == "M":
                            self.mflag = 1
                       elif self.mflag == 1:
	                  if token.tok_name[id] == "STRING":
                              if spmod == "core":
                                 if self.func_name == '':
                                    strings.append( (entry[2], value) )  
                              elif self.func_name == spmod:
                                    strings.append( (entry[2], value) )
	                  elif token.tok_name[id] == "EQUAL" or token.tok_name[id] == "RPAR":
	                      self.mflag = 0



        def parseAll(self,strings,entry):

            if isinstance(entry,list):
                id = entry[0]
                value = entry[1]
                if isinstance(value,list):
                    for element in entry:
                        self.parseAll(strings,element)
                else:
	            if token.tok_name[id] == "NAME" and value == "T":
	                self.sflag = 1

	            elif self.sflag == 1:
	                if token.tok_name[id] == "LPAR":
		           self.tflag=1
		           self.bracket=1
	                self.sflag=0

	            elif self.tflag == 1:
	                 if token.tok_name[id] == "LPAR":
	                       self.bracket+=1
	                       if self.bracket>1:
	                           self.outstr += '('
	                 elif token.tok_name[id] == "RPAR":
                               self.bracket-=1
	                       if self.bracket>0:
	                            self.outstr += ')'
	                       else:
	                          strings.append( (entry[2], self.outstr) )
	                          self.outstr=''
	                          self.tflag=0

	                 elif self.bracket>0:
	                      self.outstr += value

                    else:

	               if token.tok_name[id] == "NAME" and value == "M":
	                  self.mflag = 1

	               elif self.mflag == 1:

	                  if token.tok_name[id] == "STRING":
	                      strings.append( (entry[2], value) )

	                  elif token.tok_name[id] == "EQUAL" or token.tok_name[id] == "RPAR":
	                      self.mflag = 0

	       

def findstr(fileName,spmod,modlist):
    """
      Using the Parse Tree to extract the strings to be translated
    """
    try:
        file = open(fileName)
    except:
        path = os.path.split(__file__)[0]
        fileName = os.path.join(path,fileName)
        try:
            file = open(fileName)
        except:
            return
	    
    fileContent = file.read()
    fileContent = fileContent.replace("\r","") + '\n'

    try:
      st = parser.suite(fileContent)
      stList = parser.st2list(st,line_info=1)
    
      strings = []

      P = ParseFiles()
      
      if spmod == "ALL" :
         for element in stList:
            P.parseAll(strings,element)
      else:
        if fileName.endswith("/eden/modules/eden/menus.py") == True :
           for element in stList:
              P.parseMenu(spmod,strings,element,0)
        elif fileName.endswith("/eden/modules/s3cfg.py") == True:
           for element in stList:
              P.parseS3cfg(spmod,strings,element,modlist)
        elif fileName.endswith("/eden/models/000_config.py") == True:
           for element in stList:
              P.parseConfig(spmod,strings,element,modlist)

      return strings

    except:
       return []    
