#!/usr/bin/python
import sys
import os
import parser
import symbol
import token

tflag = 0
mflag = 0
cflag = 0
fflag = 0
sflag = 0
bracket = 0;
outstr= ''
class_name=''
func_name = ''
findent = -1

def parseMenu(spmod,strings,entry,level):

    global tflag,sflag,cflag,fflag,bracket,outstr,mflag,class_name,func_name,findent

    if isinstance(entry,list):
        id = entry[0]
        value = entry[1]
        if isinstance(value,list):
            for element in entry:
                parseMenu(spmod,strings,element,level+1)
        else:
	    if cflag == 1:
	       class_name = value
	       cflag = 0

	    elif token.tok_name[id] == "NAME" and value == "class":
	       cflag = 1
	 
            elif fflag == 1:
               func_name = value
               fflag=0

	    elif token.tok_name[id] == "NAME" and value == "def" and (findent == -1 or level == findent) :
               if class_name == "S3OptionsMenu": 
		 findent = level
	         fflag = 1
	       else:
	         func_name = ''

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
		           if spmod == "core":
                              if func_name == '':
	                        strings.append( (entry[2], outstr) )  
                           elif func_name == spmod:
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
                      if spmod == "core":
                         if func_name == '':
                            strings.append( (entry[2], value) )  
                      elif func_name == spmod:
                            strings.append( (entry[2], value) )
	          elif token.tok_name[id] == "EQUAL" or token.tok_name[id] == "RPAR":
	              mflag = 0



def parseAll(strings,entry):
    global tflag,sflag,bracket,outstr,mflag

    if isinstance(entry,list):
        id = entry[0]
        value = entry[1]
        if isinstance(value,list):
            for element in entry:
                parseAll(strings,element)
        else:
	    if token.tok_name[id] == "NAME" and value == "T":
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
	              strings.append( (entry[2], value) )

	          elif token.tok_name[id] == "EQUAL" or token.tok_name[id] == "RPAR":
	              mflag = 0

	       

def findstr(fileName,spmod):
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
      
      if spmod == "ALL" :
        for element in stList:
           parseAll(strings,element)
      else:
        if fileName.endswith("/eden/modules/eden/menus.py") == True :
          for element in stList:
           parseMenu(spmod,strings,element,0)

      return strings

    except:
       return [] 
