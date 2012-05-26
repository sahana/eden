#!/usr/bin/python
import sys
import os
import parser
import symbol
import token

tflag = 0
sflag = 0
mflag = 0
bracket = 0;
outstr=''

def parseList(entry,level):
    global tflag,sflag, bracket,outstr,mflag
    if isinstance(entry,list):
        id = entry[0]
        value = entry[1]
        if isinstance(value,list):
            for element in entry:
                parseList(element, level+1)
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
	                   print entry[2], outstr
	                   outstr=''
	                   tflag=0
	         elif bracket>0:
	              outstr += value
            else:
	       if token.tok_name[id] == "NAME" and value == "M":
	          mflag = 1
	       elif mflag == 1:
	          if token.tok_name[id] == "STRING":
	             print entry[2], value
	          elif token.tok_name[id] == "EQUAL" or token.tok_name[id] == "RPAR":
	              mflag = 0

	       
                 
                   
    #        print "%s%s: %s %s" % (" "*level ,token.tok_name[id], value, entry[2])

def _main():
    """
      Using the Parse Tree to extract the strings to be translated
    """
    if len(sys.argv) == 1:
        print "Please add a python file to process"
        return

    global tflag
    tflag=0

    fileName = sys.argv[1]

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
    st = parser.suite(fileContent)
    stList = parser.st2list(st,line_info=1)
    print fileName
    for element in stList:
        parseList(element, 0)

if __name__ == '__main__':
    _main()
