#!/usr/bin/python

import os
import sys
import parser
import symbol
import token
import csv
from subprocess import call
from gluon import current

try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO


class TranslateGetFiles:

        """Class to group files by modules"""

        def __init__(self):

            """Set up dictionary with files grouped by modules"""

            self.d = {}
            self.rest_dirs = []
            # Retrieve a list of eden modules
            self.modlist = self.get_module_list()

            for m in self.modlist:
                self.d[m] = []

            # List of files belonging to 'core' module
            self.d["core"] = []

            # 'special' files which contain strings from more than one module
            self.d["special"] = []

            # Directories which are not required to be searched
            self.rest_dirs = ["languages", "deployment-templates", "docs",
            "tests", "test", ".git", "TranslationFunctionality", "private"]

        #----------------------------------------------------------------------
        def get_module_list(self):

            """
                Returns a list of modules using files in /eden/controllers/
                as point of reference
            """

            mod = []
            base_dir = os.path.join(os.getcwd(), "applications",\
                       current.request.application)
            cont_dir = os.path.join(base_dir, "controllers")
            mod_files = os.listdir(cont_dir)

            for f in mod_files:
                if f[0] != '.':
                    mod.append(f[:-3])

            return mod

        #----------------------------------------------------------------------
        def group_files(self, currentDir, curmod, vflag):

            """
                Recursive function to group Eden files into respective modules
            """

            currentDir = os.path.abspath(currentDir)
            base_dir = os.path.basename(currentDir)

            if base_dir in self.rest_dirs:
                return

            # If current directory is '/eden/views', set vflag
            if base_dir == "views":
                vflag=1

            files = os.listdir(currentDir)

            for f in files:
                curFile = os.path.join(currentDir, f)
                if os.path.isdir(curFile):

                     # If the current directory is /eden/views,
                     #categorize files based on the directory name
                    if base_dir=="views":
                        self.group_files(curFile, os.path.basename(curFile),\
                                         vflag)
                    else:
                        self.group_files(curFile, curmod, vflag)

                elif (curFile.endswith("test.py") or \
                      curFile.endswith("tests.py")) == False:

                    # If in /eden/views, categorize by parent directory name
                    if vflag==1:
                        base = curmod

                    # Categorize file as "special" as it contains strings
                    # belonging to various modules
                    elif curFile.endswith("/eden/modules/eden/menus.py") or \
                         curFile.endswith("/eden/modules/s3cfg.py") or \
                         curFile.endswith("/eden/models/000_config.py"):
                        base = "special"
                    else:
                        # Removing '.py'
                        base = os.path.splitext(f)[0]

                        # If file is inside /eden/modules/s3 directory and
                        # has "s3" as prefix, remove "s3" to get module name
                        if base_dir == "s3" and "s3" in base:
                            base = base[2:]

                        # If file is inside /eden/models and file name is
                        # of the form var_module.py, remove the "var_" prefix
                        elif base_dir == "models" and "_" in base:
                            base = base.split('_')[1]

                    # If base refers to a module, append to corresponding list
                    if base in self.d.keys():
                        self.d[base].append(curFile)
                    # else append it to "core" files list
                    else:
                        self.d["core"].append(curFile)

#==============================================================================

class TranslateAPI:

        """
            API class for the Translation module to get
            files,modules and strings individually
        """

        def __init__(self):

            base_dir = os.path.join(os.getcwd(), "applications",\
                                   current.request.application)
            self.grp = TranslateGetFiles()
            self.grp.group_files(base_dir, '', 0)

        #------------------------------------------------------------------
        def get_modules(self):
            return self.grp.modlist

        #------------------------------------------------------------------
        def get_files_by_module(self, module):

            """ Return a list of files corresponding to a module """

            if module in self.grp.d.keys():
                return self.grp.d[module]
            else:
                print "Module '%s' doesn't exist!" %module
                return []

        #--------------------------------------------------------------------
        def get_strings_by_module(self, module):

            """ Return a list of strings corresponding to a module """

            if module in self.grp.d.keys():
                fileList = self.grp.d[module]
            else:
                print "Module '%s' doesn't exist!" %module
                return []

            strings = []
            tmpstr = []

            R = TranslateReadFiles()

            for f in fileList:
                if f.endswith(".py") == True:
                    tmpstr = R.findstr(f, "ALL", self.grp.modlist)
                    for s in tmpstr:
                        strings.append((f+":"+str(s[0]), s[1]))

            # Handling "special" files separately
            fileList = self.grp.d["special"]
            for f in fileList:
                if f.endswith(".py") == True:
                    tmpstr = R.findstr(f, module, self.grp.modlist)
                    for s in tmpstr:
                        strings.append((f+":"+str(s[0]), s[1]))
            return strings

        #----------------------------------------------------------------------
        def get_strings_by_file(self, filename):

            """ Return a list of strings in a given file """

            if os.path.isfile(filename):
                filename = os.path.abspath(filename)
            else:
                print  "'%s' is not a valid file path!"%filename
                return []

            R = TranslateReadFiles()

            if filename.endswith(".py") == True:
                strings = []
                tmpstr = R.findstr(filename, "ALL", self.grp.modlist)
                for s in tmpstr:
                    strings.append((filename+":"+str(s[0]), s[1]))
                return strings
            else:
                print "Please enter a '.py' file path"
                return []

#==============================================================================

class TranslateParseFiles:

        """
            Class to extract strings from files depending on module and file
        """

        def __init__(self):

            """ Initializes all object variables """

            self.cflag = 0       # To indicate if next element is a class
            self.fflag = 0       # To indicate if next element is a function
            self.sflag = 0       # To indicate 'T' has just been found
            self.tflag = 0       # To indicate we are currently inside T(...)
            self.mflag = 0       # To indicate we are currently inside M(...)
            self.bracket = 0     # Acts as a counter for parenthesis in T(...)
            self.outstr = ''     # Collects all the data inside T(...)
            self.class_name = '' # Stores the current class name
            self.func_name = ''  # Stores the current function name
            self.mod_name = ''   # Stores module that the string may belong to
            self.findent = -1    # Stores indentation level in menus.py

        #----------------------------------------------------------------------
        def parseList(self, entry, tmpstr):

            """ Recursive function to extract strings from a parse tree """

            if isinstance(entry, list):
                id = entry[0]
                value = entry[1]
                if isinstance(value, list):
                    for element in entry:
                        self.parseList(element, tmpstr)
                else:
                    if token.tok_name[id] == "STRING":
                        tmpstr.append(value)

        #----------------------------------------------------------------------
        def parseConfig(self, spmod, strings, entry, modlist):

            """ Function to extract the strings from 000_config.py """

            if isinstance(entry, list):
                id = entry[0]
                value = entry[1]

                # If the element is not a root node,
                # go deeper into the tree using dfs
                if isinstance(value, list):
                    for element in entry:
                        self.parseConfig(spmod, strings, element, modlist)
                else:
                    if self.fflag == 1 and token.tok_name[id] == "NAME":
                    # Here, func_name stores the module_name of the form
                    # deployment.settings.module_name.variable
                        self.func_name = value
                        self.fflag = 0

                    # Set flag to store the module name from
                    # deployment_settings.module_name
                    elif token.tok_name[id] == "NAME" and \
                         value == "deployment_settings":
                        self.fflag = 1

                    # To get module name from deployment_setting.modules list
                    elif self.tflag == 0 and self.func_name == "modules" \
                         and token.tok_name[id] == "STRING":
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
                            # If it's not the last ')' of 'T()',
                            # append to outstr
                            if self.bracket>0:
                                self.outstr += ')'

                            # If it's the last ')', add string to list
                            else:
                                if spmod == "core":
                                    if self.func_name != "modules" and \
                                       self.func_name not in modlist:
                                        strings.append((entry[2], self.outstr))
                                elif (self.func_name == "modules" and \
                                      self.mod_name == spmod) or \
                                     (self.func_name == spmod):
                                    strings.append((entry[2], self.outstr))
                                self.outstr=''
                                self.tflag=0

                        # If we are inside 'T()', append value to outstr
                        elif self.bracket>0:
                            self.outstr += value

        #----------------------------------------------------------------------
        def parseS3cfg(self, spmod, strings, entry, modlist):

            """ Function to extract the strings from s3cfg.py """

            if isinstance(entry, list):
                id = entry[0]
                value = entry[1]
                if isinstance(value, list):
                    for element in entry:
                        self.parseS3cfg(spmod, strings, element, modlist)
                else:

                    # If value is a function name, store it in func_name
                    if self.fflag == 1:
                        self.func_name = value
                        self.fflag = 0

                    # If value is 'def', set fflag to store func_name next
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

                                    # If extracted data doesn't belong
                                    # to any other module, append to list
                                    if '_' not in self.func_name or \
                                   self.func_name.split('_')[1] not in modlist:
                                        strings.append((entry[2], self.outstr))

                                # If 'module' in  'get_module_variable()'
                                # is the requested module, append to list
                                elif '_' in self.func_name and \
                                self.func_name.split('_')[1] == spmod:
                                    strings.append((entry[2], self.outstr))
                                self.outstr=''
                                self.tflag=0
                        elif self.bracket>0:
                            self.outstr += value

        #---------------------------------------------------------------------
        def parseMenu(self, spmod, strings, entry, level):

            """ Function to extract the strings from menus.py """

            if isinstance(entry, list):
                id = entry[0]
                value = entry[1]
                if isinstance(value, list):
                    for element in entry:
                        self.parseMenu(spmod, strings, element, level+1)
                else:

                    # If value is a class name, store it in class_name
                    if self.cflag == 1:
                        self.class_name = value
                        self.cflag = 0

                    # If value is 'class', set cflag to store class name next
                    elif token.tok_name[id] == "NAME" and value == "class":
                        self.cflag = 1

                    elif self.fflag == 1:
                        # Here func_name is used to store the function names
                        # which are in 'S3OptionsMenu' class
                        self.func_name = value
                        self.fflag=0

                    # If value is "def" and it's the first function in the
                    # S3OptionsMenu class or its indentation level is equal
                    # to the first function in 'S3OptionsMenu class', then
                    # set fflag and store the indentation level in findent

                    elif token.tok_name[id] == "NAME" and value == "def" and \
                         (self.findent == -1 or level == self.findent):
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

                    # if inside 'T()', extract the data accordingly
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

                                # If the requested module is 'core' and
                                # extracted data doesn't lie inside the
                                # S3OptionsMenu class, append it to list
                                if spmod == "core":
                                    if self.func_name == '':
                                        strings.append((entry[2], self.outstr))

                                # If the function name (in S3OptionsMenu class)
                                # is equal to the module requested,
                                # then append it to list
                                elif self.func_name == spmod:
                                    strings.append((entry[2], self.outstr))
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

                            # If mflag is set and argument inside is a string,
                            # append it to list
                            if token.tok_name[id] == "STRING":
                                if spmod == "core":
                                    if self.func_name == '':
                                        strings.append((entry[2], value))
                                elif self.func_name == spmod:
                                    strings.append((entry[2], value))

                            # If current argument in 'M()' is of type arg = var
                            # or if ')' is found, unset mflag
                            elif token.tok_name[id] == "EQUAL" or \
                                 token.tok_name[id] == "RPAR":
                                self.mflag = 0

        #----------------------------------------------------------------------
        def parseAll(self, strings, entry):

            """ Function to extract all the strings from a file """

            if isinstance(entry, list):
                id = entry[0]
                value = entry[1]
                if isinstance(value, list):
                    for element in entry:
                        self.parseAll(strings, element)
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
                                strings.append((entry[2], self.outstr))
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
                                strings.append((entry[2], value))

                            elif token.tok_name[id] == "EQUAL" or \
                                 token.tok_name[id] == "RPAR":
                                self.mflag = 0

#==============================================================================

class TranslateReadFiles:

        def findstr(self, fileName, spmod, modlist):

            """
                Using the methods in TranslateParseFiles to extract the strings
                fileName -> the file to be used for extraction
                spmod -> the required module
                modlist -> a list of all modules in Eden
            """

            try:
                file = open(fileName)
            except:
                path = os.path.split(__file__)[0]
                fileName = os.path.join(path, fileName)
                try:
                    file = open(fileName)
                except:
                    return
            # Read all contents of file
            fileContent = file.read()
            # Remove CL-RF and NOEOL characters
            fileContent = fileContent.replace("\r", "") + '\n'

            P = TranslateParseFiles()

            st = parser.suite(fileContent)
            # Create a parse tree list for traversal
            stList = parser.st2list(st, line_info=1)

            # List which holds the extracted strings
            strings = []

            if spmod == "ALL":
                # If all strings are to be extracted, call ParseAll()
                for element in stList:
                    P.parseAll(strings, element)
            else:

                # Handling cases for special files which contain
                #strings belonging to different modules

                if fileName.endswith("/eden/modules/eden/menus.py") == True:
                    for element in stList:
                        P.parseMenu(spmod, strings, element, 0)

                elif fileName.endswith("/eden/modules/s3cfg.py") == True:
                    for element in stList:
                        P.parseS3cfg(spmod, strings, element, modlist)

                elif fileName.endswith("/eden/models/000_config.py") == True:
                    for element in stList:
                        P.parseConfig(spmod, strings, element, modlist)

            # Extracting strings from deployment_settings.variable() calls
            final_strings = []
            settings = current.deployment_settings
            for (loc, s) in strings:
                if s[0]!='"' and "settings." in s:

                    # Converting the call to a standard form
                    s = s.replace("current.deployment_settings", "settings")
                    s = s.replace("()", '')
                    l = s.split('.')
                    obj = settings

                    #Getting the actual value
                    for atr in l[1:]:
                        obj = getattr(obj, atr)()
                    s=obj
                final_strings.append((loc, s))

            return final_strings

        #----------------------------------------------------------------------
        def read_w2pfile(self, fileName):

            """
                Function to read a web2py language file and
                return a list of translation string pairs
            """

            file = open(fileName)
            fileContent = file.read()
            fileContent = fileContent.replace("\r", '') + '\n'
            tmpstr=[]

            # Creating a parse tree list
            st = parser.suite(fileContent)
            stList = parser.st2list(st, line_info=1)

            P = TranslateParseFiles()

            for element in stList:
                P.parseList(element, tmpstr)

            strings = []
            # Storing the strings as (original string, translated string) tuple
            for i in range(0, len(tmpstr)):
                if i%2 == 0:
                    strings.append((tmpstr[i], tmpstr[i+1]))
            return strings

        #----------------------------------------------------------------------
        def read_csvfile(self, fileName):

            """ Function to read a csv file and return a list of rows """

            data = []
            transReader = csv.reader(open(fileName, 'rb'))
            for row in transReader:
                data.append(row)
            return data

        #----------------------------------------------------------------------

#==============================================================================

class StringsToExcel:

        """Class to convert strings to .xls format"""

        def remove_quotes(self, Strings):

            """
                Function to remove single or double quotes around the strings
            """

            l = []

            for (d1, d2) in Strings:
                if (d1[0] == '"' and d1[-1] == '"') or\
                   (d1[0] == "'" and d1[-1] == "'"):
                    d1 = d1[1:-1]
                if (d2[0] == '"' and d2[-1] == '"') or\
                   (d2[0] == "'" and d2[-1] == "'"):
                    d2 = d2[1:-1]
                l.append((d1, d2))

            return l

        #----------------------------------------------------------------------
        def remove_duplicates(self, Strings):

            """
                Function to club all the duplicate strings into one row
                with ';' separated locations
            """

            uniq = {}

            for (loc, data) in Strings:
                uniq[data] = ''

            for (loc, data) in Strings:

                if uniq[data] != '':
                    uniq[data] = uniq[data] + ';' + loc
                else:
                    uniq[data] = loc

            l=[]

            for data in uniq.keys():
                l.append((uniq[data], data))

            return l

        #----------------------------------------------------------------------
        def create_spreadsheet(self, Strings):

            """
                Function to create a spreadsheet (.xls file) of strings with
                location, original string and translated string as columns
            """

            import xlwt
            from gluon.contenttype import contenttype

            response = current.response

            # Defining spreadsheet properties
            wbk = xlwt.Workbook("utf-8")
            sheet = wbk.add_sheet('Translate')
            style = xlwt.XFStyle()
            font = xlwt.Font()
            font.name = 'Times New Roman'
            style.font = font

            sheet.write(0, 0, 'location', style)
            sheet.write(0, 1, 'source', style)
            sheet.write(0, 2, 'target', style)

            row_num = 1

            # Writing the data to spreadsheet
            for (loc, d1, d2) in Strings:
                d2 = d2.decode('string-escape').decode("utf-8")
                sheet.write(row_num, 0, loc, style)
                sheet.write(row_num, 1, d1, style)
                sheet.write(row_num, 2, d2, style)
                row_num+=1

            # Setting column width
            for colx in range(0, 3):
                sheet.col(colx).width = 15000

            # Initialize output
            output = StringIO()

            # Saving the spreadsheet
            wbk.save(output)

            #Modifying headers to return the xls file for download
            filename = "trans.xls"
            disposition = "attachment; filename=\"%s\"" % filename
            response.headers["Content-Type"] = contenttype(".xls")
            response.headers["Content-disposition"] = disposition

            output.seek(0)
            return output.read()

        #----------------------------------------------------------------------
        def convert_to_xls(self, langfile, modlist, filelist):

            """
                Function to get the strings by module(s)/file(s), merge with
                those strings from existing w2p language file which are already
                translated and call the 'create_spreadsheet()' method
            """

            base_dir = os.path.join(os.getcwd(), "applications", \
                                    current.request.application)
            langdir = os.path.join(base_dir, "languages")
            langfile = os.path.join(langdir, langfile)

            NewStrings = []
            A = TranslateAPI()
            R = TranslateReadFiles()

            # Retrieve strings for a module
            for mod in modlist:
                NewStrings += A.get_strings_by_module(mod)

            # Retrieve strings in a file
            for f in filelist:
                NewStrings += A.get_strings_by_file(f)

            NewStrings = self.remove_quotes(NewStrings)
            NewStrings = self.remove_duplicates(NewStrings)
            NewStrings.sort(key=lambda tup: tup[1])

            # Retrive strings from existing w2p language file
            OldStrings = R.read_w2pfile(langfile)
            OldStrings = self.remove_quotes(OldStrings)
            OldStrings.sort(key=lambda tup: tup[0])

            # Merging those strings which were already translated earlier

            Strings = []
            i = 0
            lim = len(OldStrings)

            for (l, s) in NewStrings:

                while i<lim and OldStrings[i][0] < s:
                    i+=1

                if i!=lim and OldStrings[i][0] == s and \
                   OldStrings[i][1].startswith("*** ") == False:
                    Strings.append((l, s, OldStrings[i][1]))
                else:
                    Strings.append((l, s, ''))

            return self.create_spreadsheet(Strings)

#==============================================================================

class CsvToWeb2py:

        """ Class to convert a group of csv files to a web2py language file"""

        def write_csvfile(self, fileName, data):

            """ Function to write a list of rows into a csv file """

            # Quoting all the elements while writing
            transWriter = csv.writer(open(fileName, 'wb'), delimiter=' ',\
                                     quotechar='"', quoting = csv.QUOTE_ALL)
            transWriter.writerow(["location", "source", "target"])
            for row in data:
                transWriter.writerow(row)

        #----------------------------------------------------------------------
        def convert_to_w2p(self, csvfiles, w2pfilename, option):

            """
                Function to merge multiple translated csv files into one
                and then merge/overwrite the existing w2p language file
            """

            base_dir = os.path.join(os.getcwd(), "applications",\
                                   current.request.application)
            langdir = os.path.join(base_dir, "languages")
            w2pfilename = os.path.join(langdir, w2pfilename)

            # Dictionary to store (location,translated string)
            # with untranslated string as the key
            d = {}

            R = TranslateReadFiles()

            for f in csvfiles:
                data = R.read_csvfile(f)
                for row in data:
                    if row[1] in d.keys():
                        if d[row[1]][1] == '':
                            d[row[1]] = (row[0], row[2])
                    else:
                        d[row[1]] = (row[0], row[2])

            # If strings are to be merged with existing .py file
            if option == '-m':
                data = R.read_w2pfile(w2pfilename)
                for row in data:
                    tmprow = (row[0][1:-1], row[1][1:-1])
                    row = (tmprow[0], tmprow[1].decode('string-escape'))
                    if row[0] not in d.keys():
                        d[row[0]] = ('', row[1])

            # Created a list of sorted tuples
            # (location, original string, translated string)
            data = []
            for k in sorted(d.keys()):
                data.append([d[k][0], k, d[k][1]])

            # Create intermediate csv file
            csvfilename = w2pfilename[:-2] + "csv"
            self.write_csvfile(csvfilename, data)

            # Convert the csv file to intermediate po file
            pofilename = w2pfilename[:-2] + "po"
            call(["csv2po", "-i", csvfilename, "-o", pofilename])

            # Convert the po file to w2p language file
            call(["po2web2py", "-i", pofilename, "-o", w2pfilename])

            # Remove intermediate files
            os.unlink(pofilename)
            os.unlink(csvfilename)

        #----------------------------------------------------------------------

#END===========================================================================
