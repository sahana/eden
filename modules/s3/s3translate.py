# -*- coding: utf-8 -*-

""" Translation API

    @copyright: 2012 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

import os
import sys
import parser
import symbol
import token
import csv

from gluon import current

"""
    List of classes with description :


    TranslateAPI           : API class to retreive strings and files by module

    TranslateGetFiles      : Class to traverse the eden directory and
                             categorize files based on module

    TranslateParseFiles    : Class to parse python code using its parse tree
                             and obtain the required strings and data

    TranslateReadFiles     : Class to open a file, read its contents and build
                             a parse tree (for .py files) or use regex
                             (for html/js files) to obtain a list of strings
                             by calling methods from TranslateParseFiles

    TranslateReportStatus  : Class to report the translated percentage of each
                             language file for each module. It also updates
                             these percentages as and when required

    StringsToExcel         : Class which obtains strings for translation based
                             on given modules, adds existing translations from
                             corresponding language file to this list, and then
                             converts the list to a spreadsheet for translators

    CsvToWeb2py            : Class which reads a list of csv files containing
                             translations, merges translations, and updates
                             existing language file with new translations
"""

# =============================================================================
class TranslateAPI:
        """
            API class for the Translation module to get
            files, modules and strings individually
        """

        def __init__(self):

            self.grp = TranslateGetFiles()
            self.grp.group_files(current.request.folder, "", 0)

        # ---------------------------------------------------------------------
        def get_langcodes(self):
            """ Return a list of language codes """

            lang_list = []
            langdir = os.path.join(current.request.folder, "languages")
            files = os.listdir(langdir)

            for f in files:
                lang_list.append(f[:-3])

            return lang_list

        # ---------------------------------------------------------------------
        def get_modules(self):
            """ Return a list of modules """

            return self.grp.modlist

        # ---------------------------------------------------------------------
        def get_files_by_module(self, module):
            """ Return a list of files corresponding to a module """

            if module in self.grp.d.keys():
                return self.grp.d[module]
            else:
                print "Module '%s' doesn't exist!" %module
                return []

        # ---------------------------------------------------------------------
        def get_strings_by_module(self, module):
            """ Return a list of strings corresponding to a module """

            if module in self.grp.d.keys():
                fileList = self.grp.d[module]
            else:
                print "Module '%s' doesn't exist!" % module
                return []

            strings = []

            R = TranslateReadFiles()

            for f in fileList:

                tmpstr = []
                if f.endswith(".py") == True:
                    tmpstr = R.findstr(f, "ALL", self.grp.modlist)
                elif f.endswith(".html") == True or f.endswith(".js") == True:
                    tmpstr = R.read_html_js(f)
                for s in tmpstr:
                    strings.append((f + ":" + str(s[0]), s[1]))

            # Handle "special" files separately
            fileList = self.grp.d["special"]
            for f in fileList:

                tmpstr=[]
                if f.endswith(".py") == True:
                    tmpstr = R.findstr(f, module, self.grp.modlist)
                for s in tmpstr:
                    strings.append((f + ":" + str(s[0]), s[1]))

            return strings

        # ---------------------------------------------------------------------
        def get_strings_by_file(self, filename):
            """ Return a list of strings in a given file """

            if os.path.isfile(filename):
                filename = os.path.abspath(filename)
            else:
                print  "'%s' is not a valid file path!" % filename
                return []

            R = TranslateReadFiles()
            strings = []
            tmpstr = []

            if filename.endswith(".py") == True:
                tmpstr = R.findstr(filename, "ALL", self.grp.modlist)
            elif filename.endswith(".html") == True or \
                 filename.endswith(".js") == True:
                tmpstr = R.read_html_js(filename)
            else:
                print "Please enter a '.py', '.js' or '.html' file path"
                return []

            for s in tmpstr:
                strings.append((filename + ":" + str(s[0]), s[1]))
            return strings

# =============================================================================
class TranslateGetFiles:
        """ Class to group files by modules """

        def __init__(self):
            """
                Set up a dictionary to hold files belonging to a particular
                module with the module name as the key. Files which contain
                strings belonging to more than one module are grouped under
                the "special" key.
            """

            # The dictionary described above
            self.d = {}

            # Retrieve a list of eden modules
            self.modlist = self.get_module_list()

            # Initialize to an empty list for each key
            for m in self.modlist:
                self.d[m] = []

            # List of files belonging to 'core' module
            self.d["core"] = []

            # 'special' files which contain strings from more than one module
            self.d["special"] = []

            # Directories which are not required to be searched
            self.rest_dirs = ["languages", "deployment-templates", "docs",
                              "tests", "test", ".git",
                              "TranslationFunctionality", "uploads"
                              ]

        # ---------------------------------------------------------------------
        def get_module_list(self):
            """
                Returns a list of modules using files in /controllers/
                as point of reference
            """

            mod = []
            cont_dir = os.path.join(current.request.folder, "controllers")
            mod_files = os.listdir(cont_dir)

            for f in mod_files:
                if f[0] != ".":
                    mod.append(f[:-3])

            return mod

        # ---------------------------------------------------------------------
        def group_files(self, currentDir, curmod, vflag):
            """
                Recursive function to group Eden files into respective modules
            """

            appname = current.request.application

            currentDir = os.path.abspath(currentDir)
            base_dir = os.path.basename(currentDir)

            if base_dir in self.rest_dirs:
                return

            # If current directory is '/views', set vflag
            if base_dir == "views":
                vflag = 1

            files = os.listdir(currentDir)

            for f in files:
                curFile = os.path.join(currentDir, f)
                baseFile = os.path.basename(curFile)
                if os.path.isdir(curFile):

                    # If the current directory is /views,
                    # categorize files based on the directory name
                    if base_dir == "views":
                        self.group_files(curFile, os.path.basename(curFile),
                                         vflag)
                    else:
                        self.group_files(curFile, curmod, vflag)

                elif (baseFile == "test.py" or \
                      baseFile == "tests.py") == False:

                    # If in /eden/views, categorize by parent directory name
                    if vflag == 1:
                        base = curmod

                    # Categorize file as "special" as it contains strings
                    # belonging to various modules
                    elif curFile.endswith("/%s/modules/eden/menus.py" % appname) or \
                         curFile.endswith("/%s/modules/s3cfg.py" % appname) or \
                         baseFile == "000_config.py" or \
                         baseFile == "config.py":
                        base = "special"
                    else:
                        # Remove '.py'
                        base = os.path.splitext(f)[0]

                        # If file is inside /modules/s3 directory and
                        # has "s3" as prefix, remove "s3" to get module name
                        if base_dir == "s3" and "s3" in base:
                            base = base[2:]

                        # If file is inside /models and file name is
                        # of the form var_module.py, remove the "var_" prefix
                        elif base_dir == "models" and "_" in base:
                            base = base.split("_")[1]

                    # If base refers to a module, append to corresponding list
                    if base in self.d.keys():
                        self.d[base].append(curFile)
                    else:
                        # Append it to "core" files list
                        self.d["core"].append(curFile)

# =============================================================================
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
            self.outstr = ""     # Collects all the data inside T(...)
            self.class_name = "" # Stores the current class name
            self.func_name = ""  # Stores the current function name
            self.mod_name = ""   # Stores module that the string may belong to
            self.findent = -1    # Stores indentation level in menus.py

        # ---------------------------------------------------------------------
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

        # ---------------------------------------------------------------------
        def parseConfig(self, spmod, strings, entry, modlist):
            """ Function to extract strings from config.py / 000_config.py """

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
                         (value == "deployment_settings" or \
                          value == "settings"):
                        self.fflag = 1

                    # Get module name from deployment_setting.modules list
                    elif self.tflag == 0 and self.func_name == "modules" and \
                         token.tok_name[id] == "STRING":
                        if value[1:-1] in modlist:
                            self.mod_name = value[1:-1]

                    # If 'T' is encountered, set sflag
                    elif token.tok_name[id] == "NAME" and value == "T":
                        self.sflag = 1

                    # If sflag is set and '(' is found, set tflag
                    elif self.sflag == 1:
                        if token.tok_name[id] == "LPAR":
                            self.tflag = 1
                            self.bracket = 1
                        self.sflag = 0

                    # Check if inside 'T()'
                    elif self.tflag == 1:
                        # If '(' is encountered, append it to outstr
                        if token.tok_name[id] == "LPAR":
                            self.bracket += 1
                            if self.bracket > 1:
                                self.outstr += "("

                        elif token.tok_name[id] == "RPAR":
                            self.bracket -= 1
                            # If it's not the last ')' of 'T()',
                            # append to outstr
                            if self.bracket > 0:
                                self.outstr += ")"

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
                                self.outstr = ""
                                self.tflag = 0

                        # If we are inside 'T()', append value to outstr
                        elif self.bracket > 0:
                            self.outstr += value

        # ---------------------------------------------------------------------
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
                            self.tflag = 1
                            self.bracket = 1
                        self.sflag = 0

                    elif self.tflag == 1:
                        if token.tok_name[id] == "LPAR":
                            self.bracket += 1
                            if self.bracket > 1:
                                self.outstr += "("
                        elif token.tok_name[id] == "RPAR":
                            self.bracket -= 1
                            if self.bracket > 0:
                                self.outstr += ")"
                            else:
                                # If core module is requested
                                if spmod == "core":
                                    # If extracted data doesn't belong
                                    # to any other module, append to list
                                    if "_" not in self.func_name or \
                                       self.func_name.split("_")[1] not in modlist:
                                        strings.append((entry[2], self.outstr))

                                # If 'module' in  'get_module_variable()'
                                # is the requested module, append to list
                                elif "_" in self.func_name and \
                                     self.func_name.split("_")[1] == spmod:
                                    strings.append((entry[2], self.outstr))
                                self.outstr = ""
                                self.tflag = 0
                        elif self.bracket > 0:
                            self.outstr += value

        # ---------------------------------------------------------------------
        def parseMenu(self, spmod, strings, entry, level):
            """ Function to extract the strings from menus.py """

            if isinstance(entry, list):
                id = entry[0]
                value = entry[1]
                if isinstance(value, list):
                    for element in entry:
                        self.parseMenu(spmod, strings, element, level + 1)
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
                        self.fflag = 0

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
                            self.func_name = ""

                    # If current element is 'T', set sflag
                    elif token.tok_name[id] == "NAME" and value == "T":
                        self.sflag = 1

                    elif self.sflag == 1:
                        if token.tok_name[id] == "LPAR":
                            self.tflag = 1
                            self.bracket = 1
                        self.sflag = 0

                    # If inside 'T()', extract the data accordingly
                    elif self.tflag == 1:
                        if token.tok_name[id] == "LPAR":
                            self.bracket += 1
                            if self.bracket > 1:
                                self.outstr += "("
                        elif token.tok_name[id] == "RPAR":
                            self.bracket -= 1
                            if self.bracket > 0:
                                self.outstr += ")"
                            else:

                                # If the requested module is 'core' and
                                # extracted data doesn't lie inside the
                                # S3OptionsMenu class, append it to list
                                if spmod == "core":
                                    if self.func_name == "":
                                        strings.append((entry[2], self.outstr))

                                # If the function name (in S3OptionsMenu class)
                                # is equal to the module requested,
                                # then append it to list
                                elif self.func_name == spmod:
                                    strings.append((entry[2], self.outstr))
                                self.outstr = ""
                                self.tflag = 0
                        elif self.bracket > 0:
                            self.outstr += value

                    else:
                        # Get strings inside 'M()'
                        # If value is 'M', set mflag
                        if token.tok_name[id] == "NAME" and value == "M":
                            self.mflag = 1

                        elif self.mflag == 1:

                            # If mflag is set and argument inside is a string,
                            # append it to list
                            if token.tok_name[id] == "STRING":
                                if spmod == "core":
                                    if self.func_name == "":
                                        strings.append((entry[2], value))
                                elif self.func_name == spmod:
                                    strings.append((entry[2], value))

                            # If current argument in 'M()' is of type arg = var
                            # or if ')' is found, unset mflag
                            elif token.tok_name[id] == "EQUAL" or \
                                 token.tok_name[id] == "RPAR":
                                self.mflag = 0

        # ---------------------------------------------------------------------
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
                            self.tflag = 1
                            self.bracket = 1
                        self.sflag = 0

                    # If inside 'T', extract data accordingly
                    elif self.tflag == 1:
                        if token.tok_name[id] == "LPAR":
                            self.bracket += 1
                            if self.bracket > 1:
                                self.outstr += "("
                        elif token.tok_name[id] == "RPAR":
                            self.bracket -= 1
                            if self.bracket > 0:
                                self.outstr += ")"
                            else:
                                strings.append((entry[2], self.outstr))
                                self.outstr = ""
                                self.tflag = 0

                        elif self.bracket > 0:
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

# =============================================================================
class TranslateReadFiles:
        """ Class to open and read files """

        # ---------------------------------------------------------------------
        def findstr(self, fileName, spmod, modlist):
            """
                Using the methods in TranslateParseFiles to extract the strings
                fileName -> the file to be used for extraction
                spmod -> the required module
                modlist -> a list of all modules in Eden
            """

            try:
                f = open(fileName)
            except:
                path = os.path.split(__file__)[0]
                fileName = os.path.join(path, fileName)
                try:
                    f = open(fileName)
                except:
                    return
            # Read all contents of file
            fileContent = f.read()
            # Remove CL-RF and NOEOL characters
            fileContent = fileContent.replace("\r", "") + "\n"

            P = TranslateParseFiles()

            try:
                st = parser.suite(fileContent)
            except:
                return []

            f.close()

            # Create a parse tree list for traversal
            stList = parser.st2list(st, line_info=1)

            # List which holds the extracted strings
            strings = []

            if spmod == "ALL":
                # If all strings are to be extracted, call ParseAll()
                for element in stList:
                    P.parseAll(strings, element)
            else:
                # Handle cases for special files which contain
                # strings belonging to different modules
                appname = current.request.application
                if fileName.endswith("/%s/modules/eden/menus.py" % appname) == True:
                    for element in stList:
                        P.parseMenu(spmod, strings, element, 0)

                elif fileName.endswith("/%s/modules/s3cfg.py" % appname) == True:
                    for element in stList:
                        P.parseS3cfg(spmod, strings, element, modlist)

                elif os.path.basename(fileName) == "000_config.py" or \
                     os.path.basename(fileName) == "config.py":
                    for element in stList:
                        P.parseConfig(spmod, strings, element, modlist)

            # Extract strings from deployment_settings.variable() calls
            final_strings = []
            settings = current.deployment_settings
            for (loc, s) in strings:
                if s[0] != '"' and s[0] != "'" and "settings." in s:

                    # Convert the call to a standard form
                    s = s.replace("current.deployment_settings", "settings")
                    s = s.replace("()", "")
                    l = s.split(".")
                    obj = settings

                    # Get the actual value
                    for atr in l[1:]:
                        obj = getattr(obj, atr)()
                    s = obj
                final_strings.append((loc, s))

            return final_strings

        # ---------------------------------------------------------------------
        def read_html_js(self, filename):
            """
               Function to read and extract strings from html/js files
               using regular expressions
            """

            import re

            PY_STRING_LITERAL_RE = r'(?<=[^\w]T\()(?P<name>'\
                               + r"[uU]?[rR]?(?:'''(?:[^']|'{1,2}(?!'))*''')|"\
                               + r"(?:'(?:[^'\\]|\\.)*')|"\
                               + r'(?:"""(?:[^"]|"{1,2}(?!"))*""")|'\
                               + r'(?:"(?:[^"\\]|\\.)*"))'
            regex_trans = re.compile(PY_STRING_LITERAL_RE, re.DOTALL)

            html_js_file = open(filename)
            linecount = 0
            strings = []

            for line in html_js_file:
                linecount += 1
                occur = regex_trans.findall(line)
                for s in occur:
                    strings.append((linecount, s))

            html_js_file.close()
            return strings

        # ---------------------------------------------------------------------
        def get_user_strings(self):
            """
                Function to return the list of user-supplied strings
            """

            user_file = os.path.join(current.request.folder, "uploads", "user_strings.txt")

            strings = []
            COMMENT = "User supplied"

            if os.path.exists(user_file):
                f = open(user_file, "r")
                for line in f:
                    line = line.replace("\n", "")
                    line = line.replace("\r", "")
                    strings.append((COMMENT, line))
                f.close()

            return strings

        # ---------------------------------------------------------------------
        def merge_user_strings_file(self, newstrings):
            """
                Function to merge the existing file of user-supplied strings
                with newly uploaded strings
            """

            user_file = os.path.join(current.request.folder, "uploads", "user_strings.txt")

            oldstrings = []

            if os.path.exists(user_file):
                f = open(user_file, "r")
                for line in f:
                    oldstrings.append(line)
                f.close()

            # Append user strings if not already present
            f = open(user_file, "a")
            for s in newstrings:
                if s not in oldstrings:
                    f.write(s)

            f.close()

        # ---------------------------------------------------------------------
        def read_w2pfile(self, fileName):
            """
                Function to read a web2py language file and
                return a list of translation string pairs
            """

            f = open(fileName)
            fileContent = f.read()
            fileContent = "%s\n" % fileContent.replace("\r", "")
            tmpstr = []

            # Create a parse tree list
            st = parser.suite(fileContent)
            stList = parser.st2list(st, line_info=1)

            f.close()

            P = TranslateParseFiles()

            for element in stList:
                P.parseList(element, tmpstr)

            strings = []
            # Store the strings as (original string, translated string) tuple
            for i in range(0, len(tmpstr)):
                if i%2 == 0:
                    strings.append((tmpstr[i][1:-1], tmpstr[i + 1][1:-1]))
            return strings

        # ---------------------------------------------------------------------
        def read_csvfile(self, fileName):
            """ Function to read a csv file and return a list of rows """

            data = []
            f = open(fileName, "rb")
            transReader = csv.reader(f)
            for row in transReader:
                data.append(row)
            f.close()
            return data

# =============================================================================
class TranslateReportStatus:
        """
           Class to report the percentage of translated strings for each module
           for a given language
        """

        # ---------------------------------------------------------------------
        def create_master_file(self):
            """ Function to create a master file containing all the strings """

            try:
                import cPickle as pickle
            except:
                import pickle

            A = TranslateAPI()
            modlist = A.get_modules()
            modlist.append("core")

            # List containing all the strings in the eden code
            all_strings = []
            # Dictionary keyed on modules containg the indices of strings
            # in all_strings which belong to the corresponding module
            string_dict = {}
            ind = 0

            for mod in modlist:
                string_dict[mod] = []
                strings = A.get_strings_by_module(mod)
                for (l, s) in strings:
                    # Removing quotes around the strings
                    if (s[0] == '"' and s[-1] == '"') or\
                       (s[0] == "'" and s[-1] == "'"):
                        s = s[1:-1]

                    if s not in all_strings:
                        all_strings.append(s)
                        string_dict[mod].append(ind)
                        ind += 1
                    else:
                        tmpind = all_strings.index(s)
                        string_dict[mod].append(tmpind)

            # Save all_strings and string_dict as pickle objects in a file
            data_file = os.path.join(current.request.folder, "uploads", "temp.pkl")

            f = open(data_file, "wb")
            pickle.dump(all_strings, f)
            pickle.dump(string_dict, f)
            f.close()

            # Set the update flag for all languages to indicate that the
            # previously stored percentages of translation may have changed
            # as the master file has been changed.
            utable = current.s3db.translate_update
            current.db(utable.id > 0).update(sbit=True)

        # ---------------------------------------------------------------------
        def update_percentages(self, lang_code):
            """
               Function to update the translation percentages for all modules
               for a given language
            """

            try:
                import cPickle as pickle
            except:
                import pickle

            base_dir = current.request.folder
            langfile = "%s.py" % lang_code
            langfile = os.path.join(base_dir, "languages", langfile)

            # Read the language file
            R = TranslateReadFiles()
            lang_strings = R.read_w2pfile(langfile)

            # translated_strings contains those strings which are translated
            translated_strings = []
            for (s1, s2) in lang_strings:
                if not s2.startswith("*** "):
                    if s1 != s2 or lang_code == "en-gb":
                        translated_strings.append(s1)

            # Retrieve the data stored in master file
            data_file = os.path.join(base_dir, "uploads", "temp.pkl")
            f = open(data_file, "rb")
            all_strings = pickle.load(f)
            string_dict = pickle.load(f)
            f.close()

            db = current.db
            ptable = current.s3db.translate_percentage
            for mod in string_dict.keys():

                count = 0

                for ind in string_dict[mod]:
                    string = all_strings[ind]
                    if string in translated_strings:
                        count += 1

                # Update the translation count in the table
                query = (ptable.code == lang_code) & \
                        (ptable.module == mod)
                db(query).update(translated = count,
                                 untranslated = len(string_dict[mod]) - count)

        # ---------------------------------------------------------------------
        def get_translation_percentages(self, lang_code):
            """
            """

            pickle_file = os.path.join(current.request.folder, "uploads", "temp.pkl")
            # If master file doesn't exist, create it
            if not os.path.exists(pickle_file):
                self.create_master_file()

            db = current.db
            s3db = current.s3db
            ptable = s3db.translate_percentage
            utable = s3db.translate_update

            A = TranslateAPI()
            modlist = A.get_modules()
            modlist.append("core")

            query = (utable.code == lang_code)
            row = db(query).select()

            # If the translation percentages for the given language hasn't been
            # calculated earlier, add the row corresponding to that language
            # in the table and call the update_percentages() method
            if not row:
                utable.insert(code = lang_code,
                              sbit = False)
                for mod in modlist:
                    ptable.insert(code = lang_code,
                                  module = mod,
                                  translated = 0,
                                  untranslated = 0)
                self.update_percentages(lang_code)
            else:
                for r in row:
                    # If the update bit for the language is set,
                    # then update the percentages
                    if r.sbit == True:
                        self.update_percentages(lang_code)
                        db(query).update(sbit = False)

            # Dictionary keyed on modules to store percentage for each module
            percent_dict = {}
            # Total number of translated strings for the given language
            total_translated = 0
            # Total number of untranslated strings for the given language
            total_untranslated = 0
            query = (ptable.code == lang_code)
            rows = db(query).select()
            # Display the translation percentage for each module
            # by fetching the data from the table
            for row in rows:
                total_translated += row.translated
                total_untranslated += row.untranslated
                percent_dict[row.module] = \
                  (float(row.translated) / (row.translated + row.untranslated)) * 100
            percent_dict["complete_file"] = \
            (float(total_translated) / (total_translated + total_untranslated)) * 100

            # Round off the percentages to 2 decimal places
            for mod in percent_dict.keys():
                percent_dict[mod] = round(percent_dict[mod], 2)

            # Return the dictionary
            return percent_dict

# =============================================================================
class StringsToExcel:
        """ Class to convert strings to .xls format """

        # ---------------------------------------------------------------------
        def remove_quotes(self, Strings):
            """
                Function to remove single or double quotes around the strings
            """

            l = []

            for (d1, d2) in Strings:
                if (d1[0] == '"' and d1[-1] == '"') or \
                   (d1[0] == "'" and d1[-1] == "'"):
                    d1 = d1[1:-1]
                if (d2[0] == '"' and d2[-1] == '"') or \
                   (d2[0] == "'" and d2[-1] == "'"):
                    d2 = d2[1:-1]
                l.append((d1, d2))

            return l

        # ---------------------------------------------------------------------
        def remove_duplicates(self, Strings):
            """
                Function to club all the duplicate strings into one row
                with ";" separated locations
            """

            uniq = {}

            for (loc, data) in Strings:
                uniq[data] = ""

            for (loc, data) in Strings:

                if uniq[data] != "":
                    uniq[data] = uniq[data] + ";" + loc
                else:
                    uniq[data] = loc

            l=[]

            for data in uniq.keys():
                l.append((uniq[data], data))

            return l

        # ---------------------------------------------------------------------
        def create_spreadsheet(self, Strings):
            """
                Function to create a spreadsheet (.xls file) of strings with
                location, original string and translated string as columns
            """

            try:
                from cStringIO import StringIO    # Faster, where available
            except:
                from StringIO import StringIO
            import xlwt

            from gluon.contenttype import contenttype

            # Define spreadsheet properties
            wbk = xlwt.Workbook("utf-8")
            sheet = wbk.add_sheet("Translate")
            style = xlwt.XFStyle()
            font = xlwt.Font()
            font.name = "Times New Roman"
            style.font = font

            sheet.write(0, 0, "location", style)
            sheet.write(0, 1, "source", style)
            sheet.write(0, 2, "target", style)

            row_num = 1

            # Write the data to spreadsheet
            for (loc, d1, d2) in Strings:
                d2 = d2.decode("string-escape").decode("utf-8")
                sheet.write(row_num, 0, loc, style)
                sheet.write(row_num, 1, d1, style)
                sheet.write(row_num, 2, d2, style)
                row_num += 1

            # Set column width
            for colx in range(0, 3):
                sheet.col(colx).width = 15000

            # Initialize output
            output = StringIO()

            # Save the spreadsheet
            wbk.save(output)

            # Modify headers to return the xls file for download
            filename = "trans.xls"
            disposition = "attachment; filename=\"%s\"" % filename
            response = current.response
            response.headers["Content-Type"] = contenttype(".xls")
            response.headers["Content-disposition"] = disposition

            output.seek(0)
            return output.read()

        # ---------------------------------------------------------------------
        def convert_to_xls(self, langfile, modlist, filelist, filetype):
            """
                Function to get the strings by module(s)/file(s), merge with
                those strings from existing w2p language file which are already
                translated and call the "create_spreadsheet()" method if the
                default filetype "xls" is chosen. If "po" is chosen, then the
                export_to_po()" method is called.
            """

            request = current.request
            langfile = os.path.join(request.folder, "languages", langfile)

            # If the language file doesn't exist, create it
            if not os.path.exists(langfile):
                f = open(langfile, "w")
                f.write("")
                f.close()

            NewStrings = []
            A = TranslateAPI()
            R = TranslateReadFiles()

            # Retrieve strings for a module
            for mod in modlist:
                NewStrings += A.get_strings_by_module(mod)

            # Retrieve strings in a file
            for f in filelist:
                NewStrings += A.get_strings_by_file(f)

            # Remove quotes
            NewStrings = self.remove_quotes(NewStrings)
            # Add user-supplied strings
            NewStrings += R.get_user_strings()
            # Remove duplicates
            NewStrings = self.remove_duplicates(NewStrings)
            NewStrings.sort(key=lambda tup: tup[1])

            # Retrieve strings from existing w2p language file
            OldStrings = R.read_w2pfile(langfile)
            OldStrings.sort(key=lambda tup: tup[0])

            # Merge those strings which were already translated earlier
            Strings = []
            i = 0
            lim = len(OldStrings)

            for (l, s) in NewStrings:

                while i < lim and OldStrings[i][0] < s:
                    i += 1

                # Remove the prefix from the filename
                l = l.split(request.application, 1)[1]
                if i != lim and OldStrings[i][0] == s and \
                   OldStrings[i][1].startswith("*** ") == False:
                    Strings.append((l, s, OldStrings[i][1]))
                else:
                    Strings.append((l, s, ""))

            # Create excel file
            if filetype == "xls":
                return self.create_spreadsheet(Strings)
            # Create pootle file
            elif filetype == "po":
                C = CsvToWeb2py()
                return C.export_to_po(Strings)

# =============================================================================
class CsvToWeb2py:
        """ Class to convert a group of csv files to a web2py language file"""

        # ---------------------------------------------------------------------
        def write_csvfile(self, fileName, data):
            """ Function to write a list of rows into a csv file """

            f = open(fileName, "wb")

            # Quote all the elements while writing
            transWriter = csv.writer(f, delimiter=" ",\
                                     quotechar='"', quoting = csv.QUOTE_ALL)
            transWriter.writerow(["location", "source", "target"])
            for row in data:
                transWriter.writerow(row)

            f.close()

        # ---------------------------------------------------------------------
        def export_to_po(self, data):
            """ Returns a ".po" file constructed from given strings """

            from subprocess import call
            from tempfile import NamedTemporaryFile
            from gluon.contenttype import contenttype

            f = NamedTemporaryFile(delete=False)
            csvfilename = "%s.csv" % f.name
            self.write_csvfile(csvfilename, data)

            g = NamedTemporaryFile(delete=False)
            pofilename = "%s.po" % g.name
            # Shell needed on Win32
            call(["csv2po", "-i", csvfilename, "-o", pofilename], shell=True)

            h = open(pofilename, "r")

            # Modify headers to return the po file for download
            filename = "trans.po"
            disposition = "attachment; filename=\"%s\"" % filename
            response = current.response
            response.headers["Content-Type"] = contenttype(".po")
            response.headers["Content-disposition"] = disposition

            h.seek(0)
            return h.read()

        # ---------------------------------------------------------------------
        def convert_to_w2p(self, csvfiles, w2pfilename, option):
            """
                Function to merge multiple translated csv files into one
                and then merge/overwrite the existing w2p language file
            """

            from subprocess import call
            from tempfile import NamedTemporaryFile

            w2pfilename = os.path.join(current.request.folder, "languages", w2pfilename)

            # Dictionary to store (location,translated string)
            # with untranslated string as the key
            d = {}

            R = TranslateReadFiles()

            for f in csvfiles:
                data = R.read_csvfile(f)
                for row in data:
                    if row[1] in d.keys():
                        if d[row[1]][1] == "":
                            d[row[1]] = (row[0], row[2])
                    else:
                        d[row[1]] = (row[0], row[2])

            # If strings are to be merged with existing .py file
            if option == "m":
                data = R.read_w2pfile(w2pfilename)
                for row in data:
                    row = (row[0], row[1].decode("string-escape"))
                    if row[0] not in d.keys():
                        d[row[0]] = ("", row[1])

            # Created a list of sorted tuples
            # (location, original string, translated string)
            data = []
            for k in sorted(d.keys()):
                data.append([d[k][0], k, d[k][1]])

            # Create intermediate csv file
            f = NamedTemporaryFile(delete=False)
            csvfilename = "%s.csv" % f.name
            self.write_csvfile(csvfilename, data)

            # Convert the csv file to intermediate po file
            g = NamedTemporaryFile(delete=False)
            pofilename = "%s.po" % g.name
            # Shell needed for Win32
            call(["csv2po", "-i", csvfilename, "-o", pofilename], shell=True)

            # Convert the po file to w2p language file
            call(["po2web2py", "-i", pofilename, "-o", w2pfilename], shell=True)

            # Remove intermediate files
            os.unlink(pofilename)
            os.unlink(csvfilename)

# END =========================================================================
