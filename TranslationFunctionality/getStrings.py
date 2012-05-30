#!/usr/bin/python
import sys
import os
import parser
import symbol
import token

tflag = 0

def parseList(entry,level):
    global tflag
    if isinstance(entry,list):
        id = entry[0]
        value = entry[1]
        if isinstance(value,list):
            for element in entry:
                parseList(element, level+1)
        else:
	    if token.tok_name[id] == "NAME" and value == "T":
	        tflag = 1
	    elif tflag:
                 if token.tok_name[id] == "STRING" :
                       print entry[2],value
                 elif token.tok_name[id] == "RPAR":
                        tflag = 0
                   
    #        print "%s%s: %s %s" % (" "*level ,token.tok_name[id], value, entry[2])

def findstr(fileName):
    """
      Using the Parse Tree to extract the strings to be translated
    """
    global tflag
    tflag=0

    try:
        file = open(fileName)
    except:
        path = os.path.split(__file__)[0]
        fileName = os.path.join(path,fileName)
        try:
            file = open(fileName)
        except:
            return

    print "\n",fileName,"\n"

    fileContent = file.read()
    fileContent = fileContent.replace("\r",'') + '\n'

    try:
      st = parser.suite(fileContent)
      stList = parser.st2list(st,line_info=1)
      for element in stList:
        parseList(element, 0)
    except:
