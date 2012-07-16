#!/usr/bin/env python

# 
# Copyright (C) 2007-2008  Camptocamp
#  
# This file is part of MapFish Client
#  
# MapFish Client is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#  
# MapFish Client is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#  
# You should have received a copy of the GNU General Public License
# along with MapFish Client.  If not, see <http://www.gnu.org/licenses/>.
#

#
# Code taken from the OpenLayers code base
#
# Copyright (c) 2006-2007 MetaCarta, Inc., published under the Clear BSD
# license.  See http://svn.openlayers.org/trunk/openlayers/license.txt for the
# full text of the license.
#

#
# Merge multiple JavaScript source code files into one.
#
# Usage:
# This script requires source files to have dependencies specified in them.
#
# Dependencies are specified with a comment of the form:
#
#     // @requires <file path>
#
#  e.g.
#
#    // @requires Geo/DataSource.js
#
#  or (ideally) within a class comment definition
#
#     /**
#      * @class
#      *
#      * @requires lib/openlayers/OpenLayers/Layer.js
#      */
#
# This script should be executed like so:
#
#     mergejs.py <output.js> <directory> [...]
#
# e.g.
#
#     mergejs.py openlayers.js Geo/ CrossBrowser/
#
#  This example will cause the script to walk the `Geo` and
#  `CrossBrowser` directories--and subdirectories thereof--and import
#  all `*.js` files encountered. The dependency declarations will be extracted
#  and then the source code from imported files will be output to 
#  a file named `openlayers.js` in an order which fulfils the dependencies
#  specified.
#
#
# Note: This is a very rough initial version of this code.
#
# -- Copyright 2005-2007 MetaCarta, Inc. / OpenLayers project --
#

# TODO: Allow files to be excluded. e.g. `Crossbrowser/DebugMode.js`?
# TODO: Report error when dependency can not be found rather than KeyError.

import re
import os
import sys

SUFFIX_JAVASCRIPT = ".js"

RE_REQUIRE = "@requires (.*)\n" # TODO: Ensure in comment?
class SourceFile:
    """
    Represents a Javascript source code file.
    """

    def __init__(self, filepath, source):
        """
        """
        self.filepath = filepath
        self.source = source

        self.requiredBy = []


    def _getRequirements(self):
        """
        Extracts the dependencies specified in the source code and returns
        a list of them.
        """
        # TODO: Cache?
        return re.findall(RE_REQUIRE, self.source)

    requires = property(fget=_getRequirements, doc="")



def usage(filename):
    """
    Displays a usage message.
    """
    print "%s [-c <config file>] <output.js> <directory> [...]" % filename


class Config:
    """
    Represents a parsed configuration file.

    A configuration file should be of the following form:

        [first]
        3rd/prototype.js
        core/application.js
        core/params.js

        [last]
        core/api.js

        [exclude]
        3rd/logger.js

    All headings are required.

    The files listed in the `first` section will be forced to load
    *before* all other files (in the order listed). The files in `last`
    section will be forced to load *after* all the other files (in the
    order listed).

    The files list in the `exclude` section will not be imported.
    
    """

    def __init__(self, filename):
        """
        Parses the content of the named file and stores the values.
        """
        lines = [line.strip() # Assumes end-of-line character is present
                 for line in open(filename)
                 if line.strip()] # Skip blank lines

        self.forceFirst = lines[lines.index("[first]") + 1:lines.index("[last]")]

        self.forceLast = lines[lines.index("[last]") + 1:lines.index("[include]")]
        self.include =  lines[lines.index("[include]") + 1:lines.index("[exclude]")]
        self.exclude =  lines[lines.index("[exclude]") + 1:]

def getFiles(configDict, configFile = None):
    cfg = None
    if configFile:
        cfg = Config(configFile)

    ## Build array of directories
    allDirs = []
    for k, v in configDict.iteritems():
        if not v in allDirs:
            allDirs.append(v)

    allFiles = []

    ## Find all the Javascript source files
    for sourceDirectory in allDirs:
        for root, dirs, files in os.walk(sourceDirectory):
            for filename in files:
                if filename.endswith(SUFFIX_JAVASCRIPT) and not filename.startswith("."):
                    filepath = os.path.join(root, filename)[len(sourceDirectory)+1:]
                    filepath = filepath.replace("\\", "/")
                    if cfg and cfg.include:
                        if filepath in cfg.include or filepath in cfg.forceFirst:
                            allFiles.append(filepath)
                    elif (not cfg) or (filepath not in cfg.exclude):
                        allFiles.append(filepath)

    files = {}
    order = [] # List of filepaths to output, in a dependency satisfying order 

    ## Import file source code
    ## TODO: Do import when we walk the directories above?
    for filepath in allFiles:
        #print "Importing: %s" % filepath
        if "\\" in filepath:
            filekey = filepath.replace("\\", "/").split("/")[0]
        elif "/" in filepath:
            filekey = filepath.split("/")[0]
        else:
            filekey = "."
        fullpath = os.path.join(configDict[filekey], filepath)
        content = open(fullpath, "U").read() # TODO: Ensure end of line @ EOF?
        files[filepath] = SourceFile(filepath, content) # TODO: Chop path?

    #print

    from toposortmf import toposort

    complete = False
    resolution_pass = 1

    while not complete:
        order = [] # List of filepaths to output, in a dependency satisfying order 
        nodes = []
        routes = []
        ## Resolve the dependencies
        #print "Resolution pass %s... " % resolution_pass
        resolution_pass += 1 

        for filepath, info in files.items():
            nodes.append(filepath)
            for neededFilePath in info.requires:
                routes.append((neededFilePath, filepath))

        for dependencyLevel in toposort(nodes, routes):
            for filepath in dependencyLevel:
                order.append(filepath)
                if not files.has_key(filepath):
                    #print "Importing: %s" % filepath
                    if "\\" in filepath:
                        filekey = filepath.replace("\\", "/").split("/")[0]
                    elif "/" in filepath:
                        filekey = filepath.split("/")[0]
                    else:
                        filekey = "."
                    fullpath = os.path.join(configDict[filekey], filepath)
                    content = open(fullpath, "U").read() # TODO: Ensure end of line @ EOF?
                    files[filepath] = SourceFile(filepath, content) # TODO: Chop path?

        # Double check all dependencies have been met
        complete = True
        try:
            for fp in order:
                if max([order.index(rfp) for rfp in files[fp].requires] +
                       [order.index(fp)]) != order.index(fp):
                    complete = False
        except:
            complete = False
        
        #print    


    ## Move forced first and last files to the required position
    if cfg:
        #print "Re-ordering files..."
        order = cfg.forceFirst + [item
                     for item in order
                     if ((item not in cfg.forceFirst) and
                         (item not in cfg.forceLast))] + cfg.forceLast

    return (files, order)

def run (files, order, outputFilename = None):
    ## Output the files in the determined order
    result = []

    ## Header inserted at the start of each file in the output
    HEADER = "/* " + "=" * 70 + "\n    %s\n" + "   " + "=" * 70 + " */\n\n"

    for fp in order:
        f = files[fp]
        #print "Exporting: ", f.filepath
        result.append(HEADER % f.filepath)
        source = f.source
        result.append(source)
        if not source.endswith("\n"):
            result.append("\n")

    #print "\nTotal files merged: %d " % len(files)

    if outputFilename:
        #print "\nGenerating: %s" % (outputFilename)
        open(outputFilename, "w").write("".join(result))
    return "".join(result)

if __name__ == "__main__":
    import getopt

    options, args = getopt.getopt(sys.argv[1:], "-c:")
    
    try:
        outputFilename = args[0]
    except IndexError:
        usage(sys.argv[0])
        raise SystemExit
    else:
        sourceDirectory = args[1]
        if not sourceDirectory:
            usage(sys.argv[0])
            raise SystemExit

    configDict = { 'OpenLayers': sourceDirectory }

    configFile = None
    if options and options[0][0] == "-c":
        configFile = options[0][1]
        print "Parsing configuration file: %s" % filename

    run(configDict, outputFilename, configFile)
