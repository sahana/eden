#!/usr/bin/python

import sys
import os
import parser
import symbol
import token

class ParseFiles:

	""" Class to extract strings from files depending on the module and file"""

        def __init__(self):

	    """ Initializes all object variables """

            self.cflag = 0       # To indicate if the next element of the parse tree is the name of a class
            self.fflag = 0       # To indicate if the next element of the parse tree is the name of a function
            self.sflag = 0       # To indicate that 'T' function has just been found and the next element must be '('
            self.tflag = 0       # To indicate that we are currently inside T(...)
            self.mflag = 0       # To indicate that we are currently inside M(...)
            self.bracket = 0     # Acts as a counter for the parenthesis in T(...)
            self.outstr = ''     # Collects all the data inside T(...)
            self.class_name = '' # Stores the current class name
            self.func_name = ''  # Stores the current function name
            self.mod_name = ''   # Denotes the module to which the string/data may belong
            self.findent = -1    # Denotes the indentation level of module specific functions in menus.py
        
        #--------------------------------------------------------------------------------------------------------------------------    

        def parseConfig(self,spmod,strings,entry,modlist):   
             
            """ Function to extract the strings from 000_config.py """

            if isinstance(entry,list):
               id = entry[0]
	       value = entry[1]
               if isinstance(value,list):                                 # If the element is not a root node, go deeper into the tree using dfs
		    for element in entry:
		        self.parseConfig(spmod,strings,element,modlist)
               else:
                  if self.fflag == 1 and token.tok_name[id] == "NAME":    
                     self.func_name = value                               # Here, func_name stores the module_name from code that contains 
                     self.fflag = 0                                       # deployment.settings.module_name.some_variable

                  elif token.tok_name[id] == "NAME" and value == "deployment_settings":     # If the line is of the form deployment_settings.any_name
                      self.fflag = 1                                                        # then set the flag to store the module_name

	          elif self.tflag == 0 and self.func_name == "modules" and token.tok_name[id] == "STRING":  # To get the module name from
                      if value[1:-1] in modlist:                                                            # deployment_setting.modules list
	                 self.mod_name = value[1:-1]

                  elif token.tok_name[id] == "NAME" and value == "T":     # If 'T' is encountered, set sflag
                      self.sflag = 1

                  elif self.sflag == 1:                                  # If sflag is set and '(' is found, then set tflag and increment bracket 
	             if token.tok_name[id] == "LPAR":
		        self.tflag=1
		        self.bracket=1
	             self.sflag=0

	          elif self.tflag == 1:                                  # To check if we are inside 'T()' 
	               if token.tok_name[id] == "LPAR":                  # If '(' is encountered, append it to outstr and increment bracket
	                    self.bracket+=1
	                    if self.bracket>1:
	                       self.outstr += '('
	               elif token.tok_name[id] == "RPAR":                # If ')' is encountered , decrement bracket
                            self.bracket-=1
	                    if self.bracket>0:                           # If it's not the last ')' of 'T()', append it to outstr
	                        self.outstr += ')'
	                    else:                                        # If its the last ')' of 'T()', then
		               if spmod == "core":                       # depending on the requested module, add the string to the list
                                  if self.func_name != "modules" and self.func_name not in modlist:  
	                            strings.append( (entry[2], self.outstr) )  
                               elif (self.func_name == "modules" and self.mod_name == spmod) or (self.func_name == spmod):
	                            strings.append( (entry[2], self.outstr) )
	                       self.outstr=''                             # unset tflag and clear outstr
	                       self.tflag=0
	               elif self.bracket>0:                               # If we are inside 'T()', then append the data to outstr
	                   self.outstr += value
                
        #--------------------------------------------------------------------------------------------------------------------------- 
        
        def parseS3cfg(self,spmod,strings,entry,modlist):

             """ Function to extract the strings from s3cfg.py """

             if isinstance(entry,list):
                id = entry[0]
                value = entry[1]
                if isinstance(value,list):
		    for element in entry:
		        self.parseS3cfg(spmod,strings,element,modlist)
                else:
                  if self.fflag == 1:                    # If the current element is a function name, store it in func_name
                      self.func_name = value
                      self.fflag = 0
	          elif token.tok_name[id] == "NAME" and value == "def":    # If the current element is 'def', then set fflag
                      self.fflag = 1
                  
                  elif token.tok_name[id] == "NAME" and value == "T":      # If 'T' is encountered, set sflag
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
			        # If core module is requested and the extracted data doesn't belong to any other module, then append to strings list
                                  if '_' not in self.func_name or self.func_name.split('_')[1] not in modlist:  
	                            strings.append( (entry[2], self.outstr) )  
	                        # If the function name is of the form get_module_variable and module is the requested module, then append to strings list
                               elif '_' in self.func_name and self.func_name.split('_')[1] == spmod:        
	                            strings.append( (entry[2], self.outstr) )
	                       self.outstr=''
	                       self.tflag=0
	               elif self.bracket>0:
	                   self.outstr += value

        #-----------------------------------------------------------------------------------------------------------------------------			   

        def parseMenu(self,spmod,strings,entry,level):

            """ Function to extract the strings from menus.py """

            if isinstance(entry,list):
                id = entry[0]
                value = entry[1]
                if isinstance(value,list):
                    for element in entry:
                        self.parseMenu(spmod,strings,element,level+1)
                else:
	            if self.cflag == 1:                                  # If the current element is a class name, then store it in class_name
	               self.class_name = value
	               self.cflag = 0

	            elif token.tok_name[id] == "NAME" and value == "class":    # If the current element is "class", then set the cflag
	               self.cflag = 1
	 
                    elif self.fflag == 1:                                # Here func_name is used to store the function names defined inside
                       self.func_name = value                            # inside S3OptionsMenu class
                       self.fflag=0

		    # If the current element is "def" and it's the first function in the S3OptionsMenu class or its indentation level is equal to the
		    # first function in S3OptionsMenu class, then set the fflag and store the indentation level in findent

	            elif token.tok_name[id] == "NAME" and value == "def" and (self.findent == -1 or level == self.findent) : 
                       if self.class_name == "S3OptionsMenu": 
		         self.findent = level
	                 self.fflag = 1
	               else:
	                 self.func_name = ''

	            elif token.tok_name[id] == "NAME" and value == "T":        # If the current element is 'T', set sflag
	                 self.sflag = 1

	            elif self.sflag == 1:
	                if token.tok_name[id] == "LPAR":
		           self.tflag=1
		           self.bracket=1
	                self.sflag=0

	            elif self.tflag == 1:                                     # If inside 'T(...)', then extract the data accordingly
	                 if token.tok_name[id] == "LPAR":
	                       self.bracket+=1
	                       if self.bracket>1:
	                           self.outstr += '('
	                 elif token.tok_name[id] == "RPAR":
                               self.bracket-=1
	                       if self.bracket>0:
	                            self.outstr += ')'
	                       else:
			       # If the requested module is 'core' and the current extracted data doesn't lie inside the S3OptionsMenu class,
			       # then append it to the strings list
		                   if spmod == "core":
                                      if self.func_name == '':
	                                 strings.append( (entry[2], self.outstr) )  
	                       # If the function name (defined inside S3OptionsMenu class) is equal to the module requested,
	                       # then append it to the strings list
                                   elif self.func_name == spmod:
	                                 strings.append( (entry[2], self.outstr) )
	                           self.outstr=''
	                           self.tflag=0
	                 elif self.bracket>0:
	                      self.outstr += value

                    else:
	               if token.tok_name[id] == "NAME" and value == "M":                # If the current element is 'M', set the mflag
                            self.mflag = 1
                       elif self.mflag == 1:                                            # If mflag is set and the argument inside is a string,
	                  if token.tok_name[id] == "STRING":                            # append it to strings list depending on the requested module
                              if spmod == "core":
                                 if self.func_name == '':
                                    strings.append( (entry[2], value) )  
                              elif self.func_name == spmod:
                                    strings.append( (entry[2], value) )
	                  elif token.tok_name[id] == "EQUAL" or token.tok_name[id] == "RPAR":  # If the current argument inside M is of type arg = var
	                      self.mflag = 0                                                   # or if ')' is encountered, unset mflag

        #---------------------------------------------------------------------------------------------------------------

        def parseAll(self,strings,entry):

            """ Function to extract all the strings from a file """

            if isinstance(entry,list):
                id = entry[0]
                value = entry[1]
                if isinstance(value,list):
                    for element in entry:
                        self.parseAll(strings,element)
                else:
	            if token.tok_name[id] == "NAME" and value == "T":      # If the current element is 'T', then set sflag
	                self.sflag = 1

	            elif self.sflag == 1:                                  
	                if token.tok_name[id] == "LPAR":
		           self.tflag=1
		           self.bracket=1
	                self.sflag=0

	            elif self.tflag == 1:                                  # If inside 'T', extract the data accordingly
	                 if token.tok_name[id] == "LPAR":
	                       self.bracket+=1
	                       if self.bracket>1:
	                           self.outstr += '('
	                 elif token.tok_name[id] == "RPAR":
                               self.bracket-=1
	                       if self.bracket>0:
	                            self.outstr += ')'
	                       else:
	                          strings.append( (entry[2], self.outstr) )       # If the ending ')' of 'T()' is encountered, then append the data
	                          self.outstr=''                                  # extracted into the list of strings
	                          self.tflag=0

	                 elif self.bracket>0:
	                      self.outstr += value

                    else:

	               if token.tok_name[id] == "NAME" and value == "M":          # If current element is 'M', then set mflag
	                  self.mflag = 1

	               elif self.mflag == 1:                                      # If inside 'M()', then extract string accordingly and append
 	                  if token.tok_name[id] == "STRING":                      # it into the list of strings
	                      strings.append( (entry[2], value) )

	                  elif token.tok_name[id] == "EQUAL" or token.tok_name[id] == "RPAR":
	                      self.mflag = 0

	       
#===============================================================================================			      

def findstr(fileName,spmod,modlist):

    """
      Using the Parse Tree to extract the strings to be translated based on 
      fileName -> the file to be used for extraction
      spmod -> the required module
      modlist -> a list of all modules in Eden
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
	    
    fileContent = file.read()                                  # Read all contents of the file
    fileContent = fileContent.replace("\r","") + '\n'          # Converting CL-RF and NOEOL characters into linux readable format

    try:
      st = parser.suite(fileContent)                       
      stList = parser.st2list(st,line_info=1)                  # Creating the parse tree list for traversal
    
      strings = []                                             # contains a list of strings that are extracted

      P = ParseFiles()
      
      if spmod == "ALL" :                                     # If all strings are to be extracted from the file, then call ParseAll()
         for element in stList:
            P.parseAll(strings,element)
      else:

        # Handling cases for special files which contain strings belonging to different modules

        if fileName.endswith("/eden/modules/eden/menus.py") == True :     
           for element in stList:
              P.parseMenu(spmod,strings,element,0)

        elif fileName.endswith("/eden/modules/s3cfg.py") == True:
           for element in stList:
              P.parseS3cfg(spmod,strings,element,modlist)

        elif fileName.endswith("/eden/models/000_config.py") == True:
           for element in stList:
              P.parseConfig(spmod,strings,element,modlist)

      return strings                   # return a list of extracted strings

    except:
       return []    

# END ==================================================================================
