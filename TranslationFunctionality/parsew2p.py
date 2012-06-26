#!/usr/bin/python

import parser
import symbol
import token

def parseList(entry,tmpstr):
        
	 """ Recursive function to extract strings from a parse tree """

         if isinstance(entry,list):
              id = entry[0]
              value = entry[1]
              if isinstance(value,list):
                   for element in entry:
                        parseList(element,tmpstr)
              else:
                    if token.tok_name[id] == "STRING":
                        tmpstr.append(value)
																				    
#---------------------------------------------------------------------------------------------------
																				

def read_w2pfile(fileName):
             
	      """ Function to read a web2py language file and return a list of translation string pairs """
	      try:
                  file = open(fileName)
                  fileContent = file.read()
                  fileContent = fileContent.replace("\r",'') + '\n'
                  tmpstr=[]

                  # Creating a parse tree list
                  st = parser.suite(fileContent)
                  stList = parser.st2list(st,line_info=1)
	          for element in stList:
		               parseList(element,tmpstr)

	          strings = []
                  # Storing the strings as a (original string, translated string) tuple
                  for i in range(0,len(tmpstr)):
                     if i%2 == 0:
                       strings.append( (tmpstr[i],tmpstr[i+1]) )
                  return strings 
              except:
                  return []

#END===========================================================================================================
