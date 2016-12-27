# -*- coding: utf-8 -*-

""" Translation API

    @copyright: 2012-2016 (c) Sahana Software Foundation
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
import parser
import token

from gluon import current
from gluon.languages import read_dict, write_dict
from gluon.storage import Storage

from s3fields import S3ReusableField

"""
    List of classes with description :


    TranslateAPI           : API class to retrieve strings and files by module

    TranslateGetFiles      : Class to traverse the eden directory and
                             categorize files based on module

    TranslateParseFiles    : Class to extract strings to translate from code files

    TranslateReadFiles     : Class to open a file, read its contents and build
                             a parse tree (for .py files) or use regex
                             (for html/js files) to obtain a list of strings
                             by calling methods from TranslateParseFiles

    Strings                : Class to manipulate strings and their files

    Pootle                 : Class to synchronise a Pootle server's translation
                             with the local one

    TranslateReportStatus  : Class to report the translated percentage of each
                             language file for each module. It also updates
                             these percentages as and when required
"""

# =============================================================================
class TranslateAPI:
        """
            API class for the Translation module to get
            files, modules and strings individually
        """

        core_modules = ("auth", "default", "errors", "appadmin")

        def __init__(self):

            self.grp = TranslateGetFiles()
            self.grp.group_files(current.request.folder)

        # ---------------------------------------------------------------------
        @staticmethod
        def get_langcodes():
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
        def get_strings_by_module(self, module):
            """ Return a list of strings corresponding to a module """

            grp = self.grp
            d = grp.d
            if module in d.keys():
                fileList = d[module]
            else:
                current.log.warning("Module '%s' doesn't exist!" % module)
                return []

            modlist = grp.modlist
            strings = []
            sappend = strings.append

            R = TranslateReadFiles()
            findstr = R.findstr

            for f in fileList:
                if f.endswith(".py") == True:
                    tmpstr = findstr(f, "ALL", modlist)
                elif f.endswith(".html") == True or \
                     f.endswith(".js") == True:
                    tmpstr = R.read_html_js(f)
                else:
                    tmpstr = []
                for s in tmpstr:
                    sappend(("%s:%s" % (f, str(s[0])), s[1]))

            # Handle "special" files separately
            fileList = d["special"]
            for f in fileList:
                if f.endswith(".py") == True:
                    tmpstr = findstr(f, module, modlist)
                    for s in tmpstr:
                        sappend(("%s:%s" % (f, str(s[0])), s[1]))

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
            sappend = strings.append
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
                sappend(("%s:%s" % (filename, str(s[0])), s[1]))
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

            # Initialize to an empty list for each module
            d = {}
            modlist = self.get_module_list(current.request.folder)
            for m in modlist:
                d[m] = []

            # List of files belonging to 'core' module
            d["core"] = []

            # 'special' files which contain strings from more than one module
            d["special"] = []

            self.d = d
            self.modlist = modlist

        # ---------------------------------------------------------------------
        @staticmethod
        def get_module_list(dir):
            """
                Returns a list of modules using files in /controllers/
                as point of reference
            """

            mod = []
            mappend = mod.append
            cont_dir = os.path.join(dir, "controllers")
            mod_files = os.listdir(cont_dir)

            for f in mod_files:
                if f[0] != ".":
                    # Strip extension
                    mappend(f[:-3])

            # Add Modules which aren't in controllers
            mod += ["support",
                    "translate",
                    ]

            return mod

        # ---------------------------------------------------------------------
        def group_files(self, currentDir, curmod="", vflag=0):
            """
                Recursive function to group Eden files into respective modules
            """

            path = os.path
            currentDir = path.abspath(currentDir)
            base_dir = path.basename(currentDir)

            if base_dir in (".git",
                            "docs",
                            "languages",
                            "private",
                            "templates", # Added separately
                            "tests",
                            "uploads",
                            ):
                # Skip
                return

            # If current directory is '/views', set vflag
            if base_dir == "views":
                vflag = 1

            d = self.d
            files = os.listdir(currentDir)

            for f in files:
                if f.startswith(".") or f.endswith(".pyc") or f in ("test.py", "tests.py"):
                    continue

                curFile = path.join(currentDir, f)
                if path.isdir(curFile):
                    # If the current directory is /views,
                    # categorize files based on the directory name
                    if vflag:
                        self.group_files(curFile, f, vflag)
                    else:
                        self.group_files(curFile, curmod, vflag)

                else:
                    # If in /appname/views, categorize by parent directory name
                    if vflag:
                        base = curmod

                    # Categorize file as "special" as it contains strings
                    # belonging to various modules
                    elif f in ("s3menus.py",
                               "s3cfg.py",
                               "000_config.py",
                               "config.py",
                               "menus.py"):
                        base = "special"
                    else:
                        # Remove extension ('.py')
                        base = path.splitext(f)[0]

                        # If file has "s3" as prefix, remove "s3" to get module name
                        if "s3" in base:
                            base = base[2:]

                        # If file is inside /models and file name is
                        # of the form var_module.py, remove the "var_" prefix
                        #elif base_dir == "models" and "_" in base:
                        #    base = base.split("_")[1]

                    # If base refers to a module, append to corresponding list
                    if base in d.keys():
                        d[base].append(curFile)
                    else:
                        # Append it to "core" files list
                        d["core"].append(curFile)

# =============================================================================
class TranslateParseFiles:
        """
            Class to extract strings to translate from code files
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
                    parseList = self.parseList
                    for element in entry:
                        parseList(element, tmpstr)
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
                    parseConfig = self.parseConfig
                    for element in entry:
                        parseConfig(spmod, strings, element, modlist)
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
                    parseS3cfg = self.parseS3cfg
                    for element in entry:
                        parseS3cfg(spmod, strings, element, modlist)
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
                    parseMenu = self.parseMenu
                    for element in entry:
                        parseMenu(spmod, strings, element, level + 1)
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
                    parseAll = self.parseAll
                    for element in entry:
                        parseAll(strings, element)
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
        """ Class to read code files """

        # ---------------------------------------------------------------------
        @staticmethod
        def findstr(fileName, spmod, modlist):
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
            f.close()

            # Remove CL-RF and NOEOL characters
            fileContent = "%s\n" % fileContent.replace("\r", "")

            try:
                st = parser.suite(fileContent)
            except:
                return []

            # Create a parse tree list for traversal
            stList = parser.st2list(st, line_info=1)

            P = TranslateParseFiles()

            # List which holds the extracted strings
            strings = []

            if spmod == "ALL":
                # If all strings are to be extracted, call ParseAll()
                parseAll = P.parseAll
                for element in stList:
                    parseAll(strings, element)
            else:
                # Handle cases for special files which contain
                # strings belonging to different modules
                appname = current.request.application
                fileName = os.path.basename(fileName)
                if fileName == "s3menus.py":
                    parseMenu = P.parseMenu
                    for element in stList:
                        parseMenu(spmod, strings, element, 0)

                elif fileName == "s3cfg.py":
                    parseS3cfg = P.parseS3cfg
                    for element in stList:
                        parseS3cfg(spmod, strings, element, modlist)

                elif fileName in ("000_config.py", "config.py"):
                    parseConfig = P.parseConfig
                    for element in stList:
                        parseConfig(spmod, strings, element, modlist)

            # Extract strings from deployment_settings.variable() calls
            final_strings = []
            fsappend = final_strings.append
            settings = current.deployment_settings
            for (loc, s) in strings:

                if s[0] != '"' and s[0] != "'":

                    # This is a variable
                    if "settings." in s:
                        # Convert the call to a standard form
                        s = s.replace("current.deployment_settings", "settings")
                        s = s.replace("()", "")
                        l = s.split(".")
                        obj = settings

                        # Get the actual value
                        for atr in l[1:]:
                            try:
                                obj = getattr(obj, atr)()
                            except:
                                current.log.warning("Can't find this deployment_setting, maybe a crud.settings", atr)
                            else:
                                s = obj
                                fsappend((loc, s))
                    else:
                        #@ToDo : Get the value of non-settings variables
                        pass

                else:
                    fsappend((loc, s))

            return final_strings

        # ---------------------------------------------------------------------
        @staticmethod
        def read_html_js(filename):
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
            findall = regex_trans.findall

            html_js_file = open(filename)
            linecount = 0
            strings = []
            sappend = strings.append

            for line in html_js_file:
                linecount += 1
                occur = findall(line)
                for s in occur:
                    sappend((linecount, s))

            html_js_file.close()
            return strings

        # ---------------------------------------------------------------------
        @staticmethod
        def get_user_strings():
            """
                Function to return the list of user-supplied strings
            """

            user_file = os.path.join(current.request.folder, "uploads",
                                     "user_strings.txt")

            strings = []
            COMMENT = "User supplied"

            if os.path.exists(user_file):
                f = open(user_file, "r")
                for line in f:
                    line = line.replace("\n", "").replace("\r", "")
                    strings.append((COMMENT, line))
                f.close()

            return strings

        # ---------------------------------------------------------------------
        @staticmethod
        def merge_user_strings_file(newstrings):
            """
                Function to merge the existing file of user-supplied strings
                with newly uploaded strings
            """

            user_file = os.path.join(current.request.folder, "uploads",
                                     "user_strings.txt")

            oldstrings = []
            oappend = oldstrings.append

            if os.path.exists(user_file):
                f = open(user_file, "r")
                for line in f:
                    oappend(line)
                f.close()

            # Append user strings if not already present
            f = open(user_file, "a")
            for s in newstrings:
                if s not in oldstrings:
                    f.write(s)

            f.close()

        # ---------------------------------------------------------------------
        @staticmethod
        def get_database_strings(all_template_flag):
            """
                Function to get database strings from csv files
                which are to be considered for translation.
            """

            from s3import import S3BulkImporter

            # List of database strings
            database_strings = []
            dappend = database_strings.append
            template_list = []
            base_dir = current.request.folder
            path = os.path
            # If all templates flag is set we look in all templates' tasks.cfg file
            if all_template_flag:
                template_dir = path.join(base_dir, "modules", "templates")
                files = os.listdir(template_dir)
                # template_list will have the list of all templates
                tappend = template_list.append
                for f in files:
                    curFile = path.join(template_dir, f)
                    baseFile = path.basename(curFile)
                    if path.isdir(curFile):
                        tappend(baseFile)
            else:
                # Set current template.
                template_list.append(current.deployment_settings.base.template)

            # List of fields which don't have an S3ReusableFiled defined but we
            # know we wish to translate
            # @ToDo: Extend to dict if we need to support some which don't just translate the name
            always_translate = ("project_beneficiary_type_id",
                                "stats_demographic_id",
                                )

            # Use bulk importer class to parse tasks.cfg in template folder
            bi = S3BulkImporter()
            S = Strings()
            read_csv = S.read_csv
            for template in template_list:
                pth = path.join(base_dir, "modules", "templates", template)
                if path.exists(path.join(pth, "tasks.cfg")) == False:
                    continue
                bi.load_descriptor(pth)

                s3db = current.s3db
                for csv in bi.tasks:
                    # Ignore special import files
                    if csv[0] != 1:
                        continue

                    # csv is in format: prefix, tablename, path of csv file
                    # assuming represent.translate is always on primary key id
                    translate = False
                    fieldname = "%s_%s_id" % (csv[1], csv[2])
                    if fieldname in always_translate:
                        translate = True
                        represent = Storage(fields = ["name"])
                    elif hasattr(s3db, fieldname) is False:
                        continue
                    else:
                        reusable_field = s3db.get(fieldname)
                        # Excludes lambdas which are in defaults()
                        # i.e. reusable fields in disabled modules
                        if reusable_field and isinstance(reusable_field, S3ReusableField):
                            represent = reusable_field.attr.represent
                            if hasattr(represent, "translate"):
                                translate = represent.translate

                    # If translate attribute is set to True
                    if translate:
                        if hasattr(represent, "fields") is False:
                            # Only name field is considered
                            fields = ["name"]
                        else:
                            # List of fields is retrieved from represent.fields
                            fields = represent.fields

                        # Consider it for translation (csv[3])
                        csv_path = csv[3]
                        try:
                            data = read_csv(csv_path)
                        except IOError:
                            # Phantom
                            continue
                        title_row = data[0]
                        idx = 0
                        idxlist = []
                        idxappend = idxlist.append
                        for e in title_row:
                            if e.lower() in fields:
                                idxappend(idx)
                            idx += 1

                        if idxlist:
                            # Line number of string retrieved.
                            line_number = 1
                            for row in data[1:]:
                                line_number += 1
                                # If string is not empty
                                for idx in idxlist:
                                    try:
                                        s = row[idx]
                                    except:
                                        current.log.error("CSV row incomplete", csv_path)
                                    if s != "":
                                        loc = "%s:%s" % (csv_path, line_number)
                                        dappend((loc, s))

            return database_strings

# =============================================================================
class Strings:
        """ Class to manipulate strings and their files """

        # ---------------------------------------------------------------------
        @staticmethod
        def remove_quotes(Strings):
            """
                Function to remove single or double quotes around the strings
            """

            l = []
            lappend = l.append

            for (d1, d2) in Strings:
                if (d1[0] == '"' and d1[-1] == '"') or \
                   (d1[0] == "'" and d1[-1] == "'"):
                    d1 = d1[1:-1]
                if (d2[0] == '"' and d2[-1] == '"') or \
                   (d2[0] == "'" and d2[-1] == "'"):
                    d2 = d2[1:-1]
                lappend((d1, d2))

            return l

        # ---------------------------------------------------------------------
        @staticmethod
        def remove_duplicates(Strings):
            """
                Function to club all the duplicate strings into one row
                with ";" separated locations
            """

            uniq = {}
            appname = current.request.application

            for (loc, data) in Strings:
                uniq[data] = ""

            for (loc, data) in Strings:

                # Remove the prefix from the filename
                loc = loc.split(appname, 1)[1]
                if uniq[data] != "":
                    uniq[data] = uniq[data] + ";" + loc
                else:
                    uniq[data] = loc

            l = []
            lappend = l.append

            for data in uniq.keys():
                lappend((uniq[data], data))

            return l

        # ---------------------------------------------------------------------
        @staticmethod
        def remove_untranslated(lang_code):
            """
                Function to remove all untranslated strings from a lang_code.py
            """

            w2pfilename = os.path.join(current.request.folder, "languages",
                                       "%s.py" % lang_code)

            data = read_dict(w2pfilename)
            #try:
            #    # Python 2.7
            #    # - won't even compile
            #    data = {k: v for k, v in data.iteritems() if k != v}
            #except:
            # Python 2.6
            newdata = {}
            for k, v in data.iteritems():
                if k != v:
                    new_data[k] = v
            data = new_data

            write_dict(w2pfilename, data)

        # ---------------------------------------------------------------------
        def export_file(self, langfile, modlist, filelist, filetype, all_template_flag):
            """
                Function to get the strings by module(s)/file(s), merge with
                those strings from existing w2p language file which are already
                translated and call the "write_xls()" method if the
                default filetype "xls" is chosen. If "po" is chosen, then the
                write_po()" method is called.
            """

            request = current.request
            settings = current.deployment_settings
            appname = request.application

            folder = request.folder
            join = os.path.join

            langcode = langfile[:-3]
            langfile = join(folder, "languages", langfile)

            # If the language file doesn't exist, create it
            if not os.path.exists(langfile):
                f = open(langfile, "w")
                f.write("")
                f.close()

            NewStrings = []
            A = TranslateAPI()

            if all_template_flag == 1:
                # Select All Templates
                A.grp.group_files(join(folder, "modules", "templates"))
            else:
                # Specific template(s) is selected
                templates = settings.get_template()
                if not isinstance(templates, (tuple, list)):
                    templates = (templates,)
                group_files = A.grp.group_files
                for template in templates:
                    template_folder = join(folder, "modules", "templates", template)
                    group_files(template_folder)

            R = TranslateReadFiles()

            ## Select Modules

            # Core Modules are always included
            core_modules = ("auth", "default")
            for mod in core_modules:
                modlist.append(mod)

            # appadmin and error are part of admin
            if "admin" in modlist:
                modlist.append("appadmin")
                modlist.append("error")

            # Select dependent modules
            models = current.models
            for mod in modlist:
                if hasattr(models, mod):
                    obj = getattr(models, mod)
                    # Currently only inv module has a depends list
                    if hasattr(obj, "depends"):
                        for element in obj.depends:
                            if element not in modlist:
                                modlist.append(element)

            get_strings_by_module = A.get_strings_by_module
            for mod in modlist:
                NewStrings += get_strings_by_module(mod)

            # Retrieve strings in a file
            get_strings_by_file = A.get_strings_by_file
            for f in filelist:
                NewStrings += get_strings_by_file(f)

            # Remove quotes
            NewStrings = self.remove_quotes(NewStrings)
            # Add database strings
            NewStrings += R.get_database_strings(all_template_flag)
            # Add user-supplied strings
            NewStrings += R.get_user_strings()
            # Remove duplicates
            NewStrings = self.remove_duplicates(NewStrings)
            NewStrings.sort(key=lambda tup: tup[1])

            # Retrieve strings from existing w2p language file
            OldStrings = self.read_w2p(langfile)
            OldStrings.sort(key=lambda tup: tup[0])

            # Merge those strings which were already translated earlier
            Strings = []
            sappend = Strings.append
            i = 0
            lim = len(OldStrings)

            for (l, s) in NewStrings:

                while i < lim and OldStrings[i][0] < s:
                    i += 1

                if i != lim and OldStrings[i][0] == s and \
                   OldStrings[i][1].startswith("*** ") == False:
                    sappend((l, s, OldStrings[i][1]))
                else:
                    sappend((l, s, ""))

            if filetype == "xls":
                # Create excel file
                return self.write_xls(Strings, langcode)
            elif filetype == "po":
                # Create pootle file
                return self.write_po(Strings)

        # ---------------------------------------------------------------------
        @staticmethod
        def read_csv(fileName):
            """ Function to read a CSV file and return a list of rows """

            import csv
            csv.field_size_limit(2**20)  # 1 Mb

            data = []
            dappend = data.append
            f = open(fileName, "rb")
            transReader = csv.reader(f)
            for row in transReader:
                dappend(row)
            f.close()
            return data

        # ---------------------------------------------------------------------
        @staticmethod
        def read_w2p(fileName):
            """
                Function to read a web2py language file and
                return a list of translation string pairs
            """

            data = read_dict(fileName)

            # Convert to list of tuples
            # @ToDo: Why?
            strings = []
            sappend = strings.append
            for s in data:
                sappend((s, data[s]))
            return strings

        # ---------------------------------------------------------------------
        @staticmethod
        def write_csv(fileName, data):
            """ Function to write a list of rows into a csv file """

            import csv

            f = open(fileName, "wb")

            # Quote all the elements while writing
            transWriter = csv.writer(f, delimiter=" ",
                                     quotechar='"', quoting = csv.QUOTE_ALL)
            transWriter.writerow(("location", "source", "target"))
            for row in data:
                transWriter.writerow(row)

            f.close()

        # ---------------------------------------------------------------------
        def write_po(self, data):
            """ Returns a ".po" file constructed from given strings """

            from subprocess import call
            from tempfile import NamedTemporaryFile
            from gluon.contenttype import contenttype

            f = NamedTemporaryFile(delete=False)
            csvfilename = "%s.csv" % f.name
            self.write_csv(csvfilename, data)

            g = NamedTemporaryFile(delete=False)
            pofilename = "%s.po" % g.name
            # Shell needed on Win32
            # @ToDo: Copy relevant parts of Translate Toolkit internally to avoid external dependencies
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
        def write_w2p(self, csvfiles, lang_code, option):
            """
                Function to merge multiple translated csv files into one
                and then merge/overwrite the existing w2p language file
            """

            w2pfilename = os.path.join(current.request.folder, "languages",
                                       "%s.py" % lang_code)

            # Dictionary to store translated strings
            # with untranslated string as the key
            data = {}

            errors = 0
            for f in csvfiles:
                newdata = self.read_csv(f)
                # Test: 2 cols or 3?
                cols = len(newdata[0])
                if cols == 1:
                    raise SyntaxError("CSV file needs to have at least 2 columns!")
                elif cols == 2:
                    # 1st column is source, 2nd is target
                    for row in newdata:
                        data[row[0]] = row[1]
                else:
                    # 1st column is location, 2nd is source, 3rd is target
                    for row in newdata:
                        data[row[1]] = row[2]

            if option == "m":
                # Merge strings with existing .py file
                keys = data.keys()
                olddata = read_dict(w2pfilename)
                for s in olddata:
                    if s not in keys:
                        data[s] = olddata[s]

            write_dict(w2pfilename, data)

        # ---------------------------------------------------------------------
        @staticmethod
        def write_xls(Strings, langcode):
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
                try:
                    sheet.write(row_num, 1, d1, style)
                except:
                    current.log.warning("Invalid source string!", loc)
                    sheet.write(row_num, 1, "", style)
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
            filename = "%s.xls" % langcode
            disposition = "attachment; filename=\"%s\"" % filename
            response = current.response
            response.headers["Content-Type"] = contenttype(".xls")
            response.headers["Content-disposition"] = disposition

            output.seek(0)
            return output.read()

# =============================================================================
class Pootle:
        """
            Class to synchronise a Pootle server's translation with the local
            one

            @ToDo: Before uploading file to Pootle, ensure all relevant
                   untranslated strings are present.
        """

        # ---------------------------------------------------------------------
        def upload(self, lang_code, filename):
            """
                Upload a file to Pootle
            """

            # @ToDo try/except error
            import mechanize
            import re

            br = mechanize.Browser()
            br.addheaders = [("User-agent", "Firefox")]

            br.set_handle_equiv(False)
            # Ignore robots.txt
            br.set_handle_robots(False)
            # Don't add Referer (sic) header
            br.set_handle_referer(False)

            settings = current.deployment_settings

            username = settings.get_L10n_pootle_username()
            if username is False:
                current.log.error("No login information found")
                return

            pootle_url = settings.get_L10n_pootle_url()
            login_url = "%saccounts/login" % pootle_url
            try:
                br.open(login_url)
            except:
                current.log.error("Connecton Error")
                return

            br.select_form("loginform")

            br.form["username"] = username
            br.form["password"] = settings.get_L10n_pootle_password()
            br.submit()

            current_url = br.geturl()
            if current_url.endswith("login/"):
                current.log.error("Login Error")
                return

            pattern = "<option value=(.+?)>%s.po" % lang_code

            # Process lang_code (if of form ab_cd --> convert to ab_CD)
            if len(lang_code) > 2:
                lang_code = "%s_%s" % (lang_code[:2], lang_code[-2:].upper())

            link = "%s%s/eden/" % (pootle_url, lang_code)

            page_source = br.open(link).read()
            # Use Regex to extract the value for field : "upload to"
            regex = re.search(pattern, page_source)
            result = regex.group(0)
            result = re.split(r'[="]', result)
            upload_code = result[2]

            try:
                br.select_form("uploadform")
                # If user is not admin then overwrite option is not there
                br.form.find_control(name="overwrite").value = ["overwrite"]
                br.form.find_control(name ="upload_to").value = [upload_code]
                br.form.add_file(open(filename), "text/plain", file_name)
                br.submit()
            except:
                current.log.error("Error in Uploading form")
                return

        # ---------------------------------------------------------------------
        def download(self, lang_code):
            """
                Download a file from Pootle

                @ToDo: Allow selection between different variants of language files
            """

            import requests
            import zipfile
            try:
                from cStringIO import StringIO    # Faster, where available
            except:
                from StringIO import StringIO
            from subprocess import call
            from tempfile import NamedTemporaryFile

            code = lang_code
            if len(lang_code) > 2:
                code = "%s_%s" % (lang_code[:2], lang_code[-2:].upper())

            pootle_url = current.deployment_settings.get_L10n_pootle_url()
            link = "%s%s/eden/export/zip" % (pootle_url, code)
            try:
                r = requests.get(link)
            except:
                current.log.error("Connection Error")
                return False

            zipf = zipfile.ZipFile(StringIO.StringIO(r.content))
            zipf.extractall()
            file_name_po = "%s.po" % lang_code
            file_name_py = "%s.py" % lang_code

            f = NamedTemporaryFile(delete=False)
            w2pfilename = "%s.py" % f.name

            call(["po2web2py", "-i", file_name_po, "-o", w2pfilename])

            S = Strings()
            path = os.path.join(current.request.folder, "languages", file_name_py)
            pystrings = S.read_w2p(path)
            pystrings.sort(key=lambda tup: tup[0])

            postrings = S.read_w2p(w2pfilename)
            # Remove untranslated strings
            postrings = [tup for tup in postrings if tup[0] != tup[1]]
            postrings.sort(key=lambda tup: tup[0])

            os.unlink(file_name_po)
            os.unlink(w2pfilename)
            return (postrings, pystrings)

        # ---------------------------------------------------------------------
        def merge_strings(self, postrings, pystrings, preference):
            """
                Merge strings from a PO file and a Py file
            """

            lim_po = len(postrings)
            lim_py = len(pystrings)
            i = 0
            j = 0

            # Store strings which are missing from pootle
            extra = []
            eappend = extra.append

            while i < lim_py and j < lim_po:
                if pystrings[i][0] < postrings[j][0]:
                    if preference == False:
                        eappend(pystrings[i])
                    i += 1
                elif pystrings[i][0] > postrings[j][0]:
                    j += 1

                # pystrings[i] == postrings[j]
                else:
                    # Pootle is being given preference
                    if preference:
                        # Check if string is not empty
                        if postrings[j][1] and not postrings[j][1].startswith("***"):
                            pystrings[i] = postrings[j]
                    # Py is being given prefernece
                    else:
                        if pystrings[i][1] and not pystrings[i][1].startswith("***"):
                            postrings[j] = pystrings[i]
                    i += 1
                    j += 1

            if preference:
                return pystrings

            else:
                # Add strings which were left
                while i < lim_py:
                    extra.append(pystrings[i])
                    i += 1
                # Add extra strings to Pootle list
                for st in extra:
                    postrings.append(st)

                postrings.sort(key=lambda tup: tup[0])
                return postrings

        # ---------------------------------------------------------------------
        def merge_pootle(self, preference, lang_code):

            # returns a tuple (postrings, pystrings)
            ret = self.download(lang_code)
            if not ret:
                return

            from subprocess import call
            from tempfile import NamedTemporaryFile
            import sys

            # returns pystrings if preference was True else returns postrings
            ret = self.merge_strings(ret[0], ret[1], preference)

            S = Strings()

            data = []
            dappend = data.append

            temp_csv = NamedTemporaryFile(delete=False)
            csvfilename = "%s.csv" % temp_csv.name

            if preference:
                # Only python file has been changed
                for i in ret:
                    dappend(("", i[0], i[1].decode("string-escape")))

                S.write_csv(csvfilename, data)
                # overwrite option
                S.write_w2p([csvfilename], lang_code, "o")

                os.unlink(csvfilename)

            else:
                # Only Pootle file has been changed
                for i in ret:
                    dappend(("", i[0], i[1].decode("string-escape")))

                S.write_csv(csvfilename, data)

                temp_po = NamedTemporaryFile(delete=False)
                pofilename = "%s.po" % temp_po.name

                # Shell needed on Win32
                # @ToDo: Copy relevant parts of Translate Toolkit internally to avoid external dependencies
                call(["csv2po", "-i", csvfilename, "-o", pofilename], shell=True)
                self.upload(lang_code, pofilename)

                # Clean up extra created files
                os.unlink(csvfilename)
                os.unlink(pofilename)

# =============================================================================
class TranslateReportStatus(object):
    """
        Class to report the percentage of translated strings for
        each module for a given language.
    """

    # -------------------------------------------------------------------------
    @classmethod
    def create_master_file(cls):
        """
            Create master file of strings and their distribution in modules
        """

        try:
            import cPickle as pickle
        except:
            import pickle

        # Instantiate the translateAPI
        api = TranslateAPI()

        # Generate list of modules
        modules = api.get_modules()
        modules.append("core")

        # The list of all strings
        all_strings = []
        addstring = all_strings.append

        # Dictionary of {module: indices of strings used in this module}
        indices = {}

        # Helper dict for fast lookups
        string_indices = {}

        index = 0
        get_strings_by_module = api.get_strings_by_module
        for module in modules:

            module_indices = []
            addindex = module_indices.append

            strings = get_strings_by_module(module)
            for (origin, string) in strings:

                # Remove outermost quotes around the string
                if (string[0] == '"' and string[-1] == '"') or\
                   (string[0] == "'" and string[-1] == "'"):
                    string = string[1:-1]

                string_index = string_indices.get(string)
                if string_index is None:
                    string_indices[string] = index
                    addstring(string)
                    addindex(index)
                    index += 1
                else:
                    addindex(string_index)

            indices[module] = module_indices

        # Save all_strings and string_dict as pickle objects in a file
        data_file = os.path.join(current.request.folder,
                                 "uploads",
                                 "temp.pkl")
        f = open(data_file, "wb")
        pickle.dump(all_strings, f)
        pickle.dump(indices, f)
        f.close()

        # Mark all string counts as dirty
        ptable = current.s3db.translate_percentage
        current.db(ptable.id > 0).update(dirty=True)

    # -------------------------------------------------------------------------
    @classmethod
    def update_string_counts(cls, lang_code):
        """
            Update the translation percentages for all modules for a given
            language.

            @ToDo: Generate fresh .py files with all relevant strings for this
                    (since we don't store untranslated strings)
        """

        try:
            import cPickle as pickle
        except:
            import pickle

        base_dir = current.request.folder

        # Read the language file
        langfile = "%s.py" % lang_code
        langfile = os.path.join(base_dir, "languages", langfile)
        lang_strings = read_dict(langfile)

        # Retrieve the data stored in master file
        data_file = os.path.join(base_dir, "uploads", "temp.pkl")
        f = open(data_file, "rb")
        all_strings = pickle.load(f)
        string_dict = pickle.load(f)
        f.close()

        db = current.db
        ptable = current.s3db.translate_percentage

        translated = set()
        addindex = translated.add
        for index, string in enumerate(all_strings):
            translation = lang_strings.get(string)
            if translation is None or translation[:4] == "*** ":
                continue
            elif translation != string or lang_code == "en-gb":
                addindex(index)

        for module, indices in string_dict.items():
            all_indices = set(indices)
            num_untranslated = len(all_indices - translated)
            num_translated = len(all_indices) - num_untranslated

            data = dict(code = lang_code,
                        module = module,
                        translated = num_translated,
                        untranslated = num_untranslated,
                        dirty=False)

            query = (ptable.code == lang_code) & \
                    (ptable.module == module)
            record = db(query).select(ptable._id, limitby=(0, 1)).first()
            if record:
                record.update_record(**data)
            else:
                ptable.insert(**data)

        return

    # -------------------------------------------------------------------------
    @classmethod
    def get_translation_percentages(cls, lang_code):
        """
            Get the percentages of translated strings per module for
            the given language code.

            @param lang_code: the language code
        """

        pickle_file = os.path.join(current.request.folder,
                                   "uploads",
                                   "temp.pkl")
        # If master file doesn't exist, create it
        if not os.path.exists(pickle_file):
            cls.create_master_file()

        db = current.db
        ptable = current.s3db.translate_percentage

        query = (ptable.code == lang_code)
        fields = ("dirty", "translated", "untranslated", "module")

        rows = db(query).select(*fields)
        if not rows or rows.first().dirty:
            # Update the string counts
            cls.update_string_counts(lang_code)
            rows = db(query).select(*fields)

        percentage = {}
        total_strings = 0
        total_translated = 0
        total_untranslated = 0
        for row in rows:

            num_translated = row.translated
            num_untranslated = row.untranslated

            total_strings += num_translated + num_untranslated

            if not num_untranslated:
                percentage[row.module] = 100
            else:
                total = num_translated + num_untranslated
                total_translated += num_translated
                total_untranslated += num_untranslated
                percentage[row.module] = \
                        round((float(num_translated) / total) * 100, 2)

        if not total_untranslated:
            percentage["complete_file"] = 100
        else:
            percentage["complete_file"] = \
                round((float(total_translated) / (total_strings)) * 100, 2)
        return percentage

# END =========================================================================
