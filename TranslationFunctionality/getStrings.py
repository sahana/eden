#!/usr/bin/python

import sys
import os
import parser
import symbol
import token

class ParseFiles:

	""" Class to extract strings from files depending on the module and file """

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

               # If the element is not a root node, go deeper into the tree using dfs	  
               if isinstance(value,list):                            
		    for element in entry:
		        self.parseConfig(spmod,strings,element,modlist)
               else:
                  if self.fflag == 1 and token.tok_name[id] == "NAME": 

                  # Here, func_name stores the module_name of the form deployment.settings.module_name.variable
                     self.func_name = value                                
                     self.fflag = 0

                  #Set flag to store the module name of deployment.settings.module_name
                  elif token.tok_name[id] == "NAME" and value == "deployment_settings": 
                      self.fflag = 1                                                    

                  # To get the module name from deployment_setting.modules list
	          elif self.tflag == 0 and self.func_name == "modules" and token.tok_name[id] == "STRING": 
                      if value[1:-1] in modlist:                                                           
	                 self.mod_name = value[1:-1]

		  # If 'T' is encountered, set sflag
                  elif token.tok_name[id] == "NAME" and value == "T": 
                      self.sflag = 1
                   
                  # If sflag is set and '(' is found, set tflag    
                  elif self.sflag == 1:                               
	             if token.tok_name[id] == "LPAR":
		        self.tflag=1
		        self.bracket=1
	             self.sflag=0

                  #Check if inside 'T()'
	          elif self.tflag == 1:

		       # If '(' is encountered, append it to outstr
	               if token.tok_name[id] == "LPAR":                 
	                    self.bracket+=1
	                    if self.bracket>1:
	                       self.outstr += '('

	               elif token.tok_name[id] == "RPAR":               
                            self.bracket-=1
                            # If it's not the last ')' of 'T()', append to outstr
	                    if self.bracket>0:                          
	                        self.outstr += ')'
			
			    # If it's the last ')', add string to list	
	                    else:                                     
		               if spmod == "core":                    
                                  if self.func_name != "modules" and self.func_name not in modlist:  
	                            strings.append( (entry[2], self.outstr) )  
                               elif (self.func_name == "modules" and self.mod_name == spmod) or (self.func_name == spmod):
	                            strings.append( (entry[2], self.outstr) )
	                       self.outstr=''                         
	                       self.tflag=0
		       
		       # If we are inside 'T()', append value to outstr		    
	               elif self.bracket>0:                             
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
		
                  # If value is a function name, store it in func_name			
                  if self.fflag == 1:                   
                      self.func_name = value
                      self.fflag = 0

                  # If value is 'def', set fflag to store the next element in func_name    
	          elif token.tok_name[id] == "NAME" and value == "def":    
                      self.fflag = 1
                 
                  # If 'T' is encountered, set sflag    
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
			       # If core module is requested
		               if spmod == "core":

		                  # If extracted data doesn't belong to any other module, append to strings list
                                  if '_' not in self.func_name or self.func_name.split('_')[1] not in modlist:  
	                            strings.append( (entry[2], self.outstr) )  

                               # If 'module' in  'get_module_variable' function is the requested module, append to strings list
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
		
		    # If value is a class name, store it in class_name	
	            if self.cflag == 1:                                 
	               self.class_name = value
	               self.cflag = 0
                    
                    # If value is 'class', set cflag to store class name next   
	            elif token.tok_name[id] == "NAME" and value == "class":   
	               self.cflag = 1
	 
                    elif self.fflag == 1:
                       # Here func_name is used to store the function names in 'S3OptionsMenu' class
                       self.func_name = value                            
                       self.fflag=0

		    # If value is "def" and it's the first function in the S3OptionsMenu class or its indentation level is equal to the
		    # first function in 'S3OptionsMenu class', then set fflag and store the indentation level in findent

	            elif token.tok_name[id] == "NAME" and value == "def" and (self.findent == -1 or level == self.findent) : 
                       if self.class_name == "S3OptionsMenu": 
		         self.findent = level
	                 self.fflag = 1
	               else:
	                 self.func_name = ''

                    # If current element is 'T', set sflag                     
	            elif token.tok_name[id] == "NAME" and value == "T":   
	                 self.sflag = 1

	            elif self.sflag == 1:
	                if token.tok_name[id] == "LPAR":
		           self.tflag=1
		           self.bracket=1
	                self.sflag=0
                   
		    # If inside 'T()', extract the data accordingly	
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

			       # If the requested module is 'core' and extracted data doesn't lie inside the S3OptionsMenu class,
			       # then append it to the strings list
		                   if spmod == "core":
                                      if self.func_name == '':
	                                 strings.append( (entry[2], self.outstr) )  

	                       # If the function name (defined in S3OptionsMenu class) is equal to the module requested,
	                       # then append it to strings list
                                   elif self.func_name == spmod:
	                                 strings.append( (entry[2], self.outstr) )
	                           self.outstr=''
	                           self.tflag=0
	                 elif self.bracket>0:
	                      self.outstr += value

                    else:
                       # To get strings inside 'M()'
                       # If value is 'M', set mflag
	               if token.tok_name[id] == "NAME" and value == "M":            
                            self.mflag = 1

                       elif self.mflag == 1:
                          # If mflag is set and the argument inside is a string,append it to strings list
	                  if token.tok_name[id] == "STRING":                            
                              if spmod == "core":
                                 if self.func_name == '':
                                    strings.append( (entry[2], value) )  
                              elif self.func_name == spmod:
                                    strings.append( (entry[2], value) )
	                  # If current argument in 'M()' is of type arg = var or if ')' is found, unset mflag
	                  elif token.tok_name[id] == "EQUAL" or token.tok_name[id] == "RPAR":  
	                      self.mflag = 0                                                   

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
		
                    # If current element is 'T', set sflag			
	            if token.tok_name[id] == "NAME" and value == "T": 
	                self.sflag = 1

	            elif self.sflag == 1:                                  
	                if token.tok_name[id] == "LPAR":
		           self.tflag=1
		           self.bracket=1
	                self.sflag=0
		
		    # If inside 'T', extract data accordingly
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
                       # If current element is 'M', set mflag
	               if token.tok_name[id] == "NAME" and value == "M":  
	                  self.mflag = 1

	               elif self.mflag == 1:                              
                          # If inside 'M()', extract string accordingly
 	                  if token.tok_name[id] == "STRING":           
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
    # Read all contents of file	    
    fileContent = file.read()  
    # Remove CL-RF and NOEOL characters
    fileContent = fileContent.replace("\r","") + '\n'

   
    st = parser.suite(fileContent)
    # Create a parse tree list for traversal	
    stList = parser.st2list(st,line_info=1)  
    
    # List which holds the extracted strings	
    strings = []                            

    P = ParseFiles()
      
    if spmod == "ALL" :                    
       # If all strings are to be extracted from the file, call ParseAll()
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

    return strings   


# END ==================================================================================
