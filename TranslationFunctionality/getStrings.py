#!/usr/bin/python
import sys
import os
import parser
import symbol
import token

tflag = 0
mflag = 0
fflag = 0
sflag = 0
bracket = 0;
outstr= ''
func_name = ''

def parseList(spmod,strings,entry,level):

    global tflag,sflag,fflag,bracket,outstr,mflag,func_name

    if isinstance(entry,list):
        id = entry[0]
        value = entry[1]
        if isinstance(value,list):
            for element in entry:
                parseList(spmod,strings,element,level+1)
        else:
            if fflag == 1:
               func_name = value
               fflag=0

	    elif spmod != "ALL" and token.tok_name[id] == "NAME" and value == "def":
	          fflag = 1 

	    elif token.tok_name[id] == "NAME" and value == "T":
	        sflag = 1

	    elif sflag == 1:
	        if token.tok_name[id] == "LPAR":
		   tflag=1
		   bracket=1
	        sflag=0

	    elif tflag:
	         if token.tok_name[id] == "LPAR":
	               bracket+=1
	               if bracket>1:
	                   outstr += '('
	         elif token.tok_name[id] == "RPAR":
                       bracket-=1
	               if bracket>0:
	                    outstr += ')'
	               else:
		           if spmod != "ALL":
                              if func_name == spmod:
	                        strings.append( (entry[2], outstr) )  
                           else:
	                      strings.append( (entry[2], outstr) )

	                   outstr=''
	                   tflag=0
	         elif bracket>0:
	              outstr += value

            else:
	       if token.tok_name[id] == "NAME" and value == "M":
	          mflag = 1
	       elif mflag == 1:

	          if token.tok_name[id] == "STRING":
                      if spmod != "ALL":
                         if func_name == spmod:
                            strings.append( (entry[2], value) )  
                      else:
	                 strings.append( (entry[2], value) )

	          elif token.tok_name[id] == "EQUAL" or token.tok_name[id] == "RPAR":
	              mflag = 0

	       
                 
                   
    #        print "%s%s: %s %s" % (" "*level ,token.tok_name[id], value, entry[2])

def findstr(fileName,spmod):
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
	    
    fileContent = file.read()
    fileContent = fileContent.replace("\r","") + '\n'

    try:
      st = parser.suite(fileContent)
      stList = parser.st2list(st,line_info=1)

      strings = []

      for element in stList:
         parseList(spmod,strings,element, 0)
      return strings

    except:
      return
