#!/usr/bin/python

import parser
import symbol
import token

def parseList(entry,tmpstr):

         if isinstance(entry,list):
              id = entry[0]
              value = entry[1]
              if isinstance(value,list):
                   for element in entry:
                        parseList(element,tmpstr)
              else:
                    if token.tok_name[id] == "STRING":
                        tmpstr.append(value)
																				    

																				

def read_w2pfile(fileName):

	      try:
                  file = open(fileName)
                  fileContent = file.read()
                  fileContent = fileContent.replace("\r",'') + '\n'
                  tmpstr=[]
                  st = parser.suite(fileContent)
                  stList = parser.st2list(st,line_info=1)
	          for element in stList:
		               parseList(element,tmpstr)

	          strings = []
                  for i in range(0,len(tmpstr)):
                     if i%2 == 0:
                       strings.append( (tmpstr[i],tmpstr[i+1]) )
                  return strings 
              except:
                  return []


