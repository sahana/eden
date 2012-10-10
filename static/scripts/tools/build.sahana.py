#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# run as:
#   python web2py.py -S eden -M -R applications/eden/static/scripts/tools/build.sahana.py
# or
#   python web2py.py -S eden -M -R applications/eden/static/scripts/tools/build.sahana.py -A gis
#
#
# Built with code/inspiration from MapFish, OpenLayers & Michael Crute
#

try:
    theme = settings.get_theme()
except:
    print "ERROR: File now needs to be run in the web2py environment in order to pick up which theme to build"
    exit()

import os
import sys
import shutil

SCRIPTPATH = os.path.join(request.folder, "static", "scripts", "tools")
os.chdir(SCRIPTPATH)

sys.path.append("./")

# For JS
import getopt
import jsmin, mergejs

# For CSS
import re

def mergeCSS(inputFilenames, outputFilename):
    output = ""
    for inputFilename in inputFilenames:
        output += open(inputFilename, "r").read()
    open(outputFilename, "w").write(output)
    return outputFilename

def cleanline(theLine):
    """ Kills line breaks, tabs, and double spaces """
    p = re.compile("(\n|\r|\t|\f|\v)+")
    m = p.sub("", theLine)

    # Kills double spaces
    p = re.compile("(  )+")
    m = p.sub(" ", m)

    # Removes last semicolon before }
    p = re.compile("(; }|;})+")
    m = p.sub("}", m)

    # Removes space before {
    p = re.compile("({ )+")
    m = p.sub("{", m)

    # Removes all comments
    p = re.compile("/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/")
    m = p.sub("", m)

    # Strip off the Charset
    p = re.compile("@CHARSET .*;")
    m = p.sub("", m)

    # Strip spaces before the {
    p = re.compile(" {")
    m = p.sub("{", m)

    # Strip space after :
    p = re.compile(": ")
    m = p.sub(":", m)

    # Strip space after ,
    p = re.compile(", ")
    m = p.sub(",", m)

    # Strip space after ;
    p = re.compile("; ")
    m = p.sub(";", m)

    return m

def compressCSS(inputFilename, outputFilename):
    theFile = open(inputFilename, "r").read()
    output = ""
    for line in theFile:
        output = output + cleanline(line)

    # Once more, clean the entire file string
    _output = cleanline(output)

    open(outputFilename, "w").write(_output)
    return

def dojs(dogis = False, warnings = True):
    """ Minifies the JavaScript """

    # Do we have local version of the Closure Compiler available?
    use_compressor = "jsmin" # Fallback
    try:
        import closure
        use_compressor = "closure"
        print "using local Closure Compiler"
    except Exception, E:
        print "No closure (%s)" % E
        print "Download from http://closure-compiler.googlecode.com/files/compiler-latest.zip"
        try:
            import closure_ws
            use_compressor = "closure_ws"
            print "Using Closure via Web Service - limited to files < 1Mb!"
        except ImportError:
            print "No closure_ws"

    if use_compressor == "closure":
        if not warnings:
            closure.extra_params = "--warning_level QUIET"
        minimize = closure.minimize
    elif use_compressor == "closure_ws":
        minimize = closure_ws.minimize
    elif use_compressor == "jsmin":
        minimize = jsmin.jsmin

    sourceDirectory = ".."
    configFilename = "sahana.js.cfg"
    outputFilename = "S3.min.js"

    # Merge JS files
    print "Merging Core libraries."
    merged = mergejs.run(sourceDirectory, None, configFilename)

    # Compress JS files
    print "Compressing - JS"
    minimized = minimize(merged)

    # Add license
    print "Adding license file."
    minimized = open("license.txt").read() + minimized

    # Print to output files
    print "Writing to %s." % outputFilename
    open(outputFilename, "w").write(minimized)

    # Remove old JS files
    print "Deleting %s." % outputFilename
    try:
        os.remove("../S3/%s" % outputFilename)
    except:
        pass

    # Move new JS files
    print "Moving new JS files"
    shutil.move(outputFilename, "../S3")

    # dataTables
    print "Compressing dataTables"
    sourceDirectorydataTables = ".."
    configFilenamedataTables = "sahana.js.dataTables.cfg"
    outputFilenamedataTables = "s3.dataTables.min.js"
    mergeddataTables = mergejs.run(sourceDirectorydataTables,
                                   None,
                                   configFilenamedataTables)
    minimizeddataTables = minimize(mergeddataTables)
    open(outputFilenamedataTables, "w").write(minimizeddataTables)
    try:
        os.remove("../S3/%s" % outputFilenamedataTables)
    except:
        pass
    shutil.move(outputFilenamedataTables, "../S3")

    # Reports
    print "Compressing Reports"
    sourceDirectoryReport = ".."
    configFilenameReport = "sahana.js.report.cfg"
    outputFilenameReport = "s3.report.min.js"
    mergedReport = mergejs.run(sourceDirectoryReport,
                               None,
                               configFilenameReport)
    minimizedReport = minimize(mergedReport)
    open(outputFilenameReport, "w").write(minimizedReport)
    try:
        os.remove("../S3/%s" % outputFilenameReport)
    except:
        pass
    shutil.move(outputFilenameReport, "../S3")

    # Vulnerability
    print "Compressing Vulnerability"
    sourceDirectoryVulnerability = ".."
    configFilenameVulnerability = "sahana.js.vulnerability.cfg"
    outputFilenameVulnerability = "s3.vulnerability.min.js"
    mergedVulnerability = mergejs.run(sourceDirectoryVulnerability,
                                      None,
                                      configFilenameVulnerability)
    minimizedVulnerability = minimize(mergedVulnerability)
    open(outputFilenameVulnerability, "w").write(minimizedVulnerability)
    try:
        os.remove("../S3/%s" % outputFilenameVulnerability)
    except:
        pass
    shutil.move(outputFilenameVulnerability, "../S3")
    print "Compressing Vulnerability GIS"
    sourceDirectoryVulnerability = "../../themes/Vulnerability/js"
    configFilenameVulnerability = "sahana.js.vulnerability_gis.cfg"
    outputFilenameVulnerability = "OpenLayers.js"
    mergedVulnerability = mergejs.run(sourceDirectoryVulnerability,
                                      None,
                                      configFilenameVulnerability)
    minimizedVulnerability = minimize(mergedVulnerability)
    open(outputFilenameVulnerability, "w").write(minimizedVulnerability)
    try:
        os.remove("../../themes/Vulnerability/js/%s" % outputFilenameVulnerability)
    except:
        pass
    shutil.move(outputFilenameVulnerability, "../../themes/Vulnerability/js")

    # Single scripts
    for filename in [
                     "contacts",
                     "embed_component",
                     "inline_component",
                     "locationselector.widget",
                     "popup",
                     "select_person",
                     "timeline",
                     ]:
        print "Compressing s3.%s.js" % filename
        inputFilename = os.path.join("..", "S3", "s3.%s.js" % filename)
        outputFilename = "s3.%s.min.js" % filename
        input = open(inputFilename, "r").read()
        minimized = minimize(input)
        open(outputFilename, "w").write(minimized)
        try:
            os.remove("../S3/%s" % outputFilename)
        except:
            pass
        shutil.move(outputFilename, "../S3")
        
    if dogis:
        sourceDirectoryGIS = "../S3"
        sourceDirectoryOpenLayers = "../gis/openlayers/lib"
        sourceDirectoryOpenLayersExten = "../gis"
        sourceDirectoryMGRS = "../gis"
        sourceDirectoryGeoExt = "../gis/GeoExt/lib"
        sourceDirectoryGeoExtux = "../gis/GeoExt/ux"
        sourceDirectoryGxp = "../gis/gxp"
        #sourceDirectoryGeoExplorer = "../gis/GeoExplorer"
        configFilenameGIS = "sahana.js.gis.cfg"
        configFilenameOpenLayers = "sahana.js.ol.cfg"
        configFilenameOpenLayersExten = "sahana.js.ol_exten.cfg"
        configFilenameMGRS = "sahana.js.mgrs.cfg"
        configFilenameGeoExt = "sahana.js.geoext.cfg"
        configFilenameGeoExtux = "sahana.js.geoextux.cfg"
        configFilenameGxpMin = "sahana.js.gxp.cfg"
        configFilenameGxpFull = "sahana.js.gxpfull.cfg"
        #configFilenameGeoExplorer = "sahana.js.geoexplorer.cfg"
        outputFilenameGIS = "s3.gis.min.js"
        outputFilenameOpenLayers = "OpenLayers.js"
        outputFilenameMGRS = "MGRS.min.js"
        outputFilenameGeoExt = "GeoExt.js"
        outputFilenameGxp = "gxp.js"
        #outputFilenameGeoExplorer = "GeoExplorer.js"

        # Merge GIS JS Files
        print "Merging GIS scripts."
        mergedGIS = mergejs.run(sourceDirectoryGIS,
                                None,
                                configFilenameGIS)

        print "Merging OpenLayers libraries."
        mergedOpenLayers = mergejs.run(sourceDirectoryOpenLayers,
                                       None,
                                       configFilenameOpenLayers)
        mergedOpenLayersExten = mergejs.run(sourceDirectoryOpenLayersExten,
                                            None,
                                            configFilenameOpenLayersExten)

        print "Merging MGRS libraries."
        mergedMGRS = mergejs.run(sourceDirectoryMGRS,
                                 None,
                                 configFilenameMGRS)

        print "Merging GeoExt libraries."
        mergedGeoExt = mergejs.run(sourceDirectoryGeoExt,
                                   None,
                                   configFilenameGeoExt)
        mergedGeoExtux = mergejs.run(sourceDirectoryGeoExtux,
                                     None,
                                     configFilenameGeoExtux)

        print "Merging gxp libraries."
        mergedGxpMin = mergejs.run(sourceDirectoryGxp,
                                   None,
                                   configFilenameGxpMin)
        mergedGxpFull = mergejs.run(sourceDirectoryGxp,
                                    None,
                                    configFilenameGxpFull)

        #print "Merging GeoExplorer libraries."
        #mergedGeoExplorer = mergejs.run(sourceDirectoryGeoExplorer,
        #                                None,
        #                                configFilenameGeoExplorer)


        # Compress JS files
        print "Compressing - GIS JS"
        minimizedGIS = minimize(mergedGIS)

        print "Compressing - OpenLayers JS"
        if use_compressor == "closure_ws":
            # Limited to files < 1Mb!
            minimizedOpenLayers = jsmin.jsmin("%s\n%s" % (mergedOpenLayers,
                                                          mergedOpenLayersExten))
        else:
            minimizedOpenLayers = minimize("%s\n%s" % (mergedOpenLayers,
                                                       mergedOpenLayersExten))

        print "Compressing - MGRS JS"
        minimizedMGRS = minimize(mergedMGRS)

        print "Compressing - GeoExt JS"
        minimizedGeoExt = minimize("%s\n%s\n%s" % (mergedGeoExt,
                                                   mergedGeoExtux,
                                                   mergedGxpMin))

        print "Compressing - gxp JS"
        minimizedGxp = minimize(mergedGxpFull)

        #print "Compressing - GeoExplorer JS"
        #minimizedGeoExplorer = minimize(mergedGeoExplorer)

        # Add license
        #minimizedGIS = open("license.gis.txt").read() + minimizedGIS

        # Print to output files
        print "Writing to %s." % outputFilenameGIS
        open(outputFilenameGIS, "w").write(minimizedGIS)

        print "Writing to %s." % outputFilenameOpenLayers
        open(outputFilenameOpenLayers, "w").write(minimizedOpenLayers)

        print "Writing to %s." % outputFilenameMGRS
        open(outputFilenameMGRS, "w").write(minimizedMGRS)

        print "Writing to %s." % outputFilenameGeoExt
        open(outputFilenameGeoExt, "w").write(minimizedGeoExt)

        print "Writing to %s." % outputFilenameGxp
        open(outputFilenameGxp, "w").write(minimizedGxp)

        #print "Writing to %s." % outputFilenameGeoExplorer
        #open(outputFilenameGeoExplorer, "w").write(minimizedGeoExplorer)

        # Move new JS files
        print "Deleting %s." % outputFilenameGIS
        try:
            os.remove("../S3/%s" % outputFilenameGIS)
        except:
            pass
        print "Moving new GIS JS files"
        shutil.move(outputFilenameGIS, "../S3")

        print "Deleting %s." % outputFilenameOpenLayers
        try:
            os.remove("../gis/%s" % outputFilenameOpenLayers)
        except:
            pass
        print "Moving new OpenLayers JS files"
        shutil.move(outputFilenameOpenLayers, "../gis")

        print "Deleting %s." % outputFilenameMGRS
        try:
            os.remove("../gis/%s" % outputFilenameMGRS)
        except:
            pass
        print "Moving new MGRS JS files"
        shutil.move(outputFilenameMGRS, "../gis")

        print "Deleting %s." % outputFilenameGeoExt
        try:
            os.remove("../gis/%s" % outputFilenameGeoExt)
        except:
            pass
        print "Moving new GeoExt JS files"
        shutil.move(outputFilenameGeoExt, "../gis")

        print "Deleting %s." % outputFilenameGxp
        try:
            os.remove("../gis/%s" % outputFilenameGxp)
        except:
            pass
        print "Moving new gxp JS files"
        shutil.move(outputFilenameGxp, "../gis")

        #print "Deleting %s." % outputFilenameGeoExplorer
        #try:
        #    os.remove("../gis/%s" % outputFilenameGeoExplorer)
        #except:
        #    pass
        #print "Moving new GeoExplorer JS files"
        #shutil.move(outputFilenameGeoExplorer, "../gis")

def docss():
    """ Compresses the  CSS files """

    listCSS = []

    theme = settings.get_theme()
    print "Using theme %s" % theme
    css_cfg = os.path.join("..", "..", "..", "private", "templates", theme, "css.cfg")
    f = open(css_cfg, "r")
    files = f.readlines()
    f.close()
    for file in files[:-1]:
        p = re.compile("(\n|\r|\t|\f|\v)+")
        file = p.sub("", file)
        listCSS.append("../../styles/%s" % file)

    outputFilenameCSS = "eden.min.css"

    # Merge CSS files
    print "Merging Core styles."
    mergedCSS = mergeCSS(listCSS, outputFilenameCSS)

    # Compress CSS files
    print "Writing to %s." % outputFilenameCSS
    compressCSS(mergedCSS, outputFilenameCSS)

    # Move files to correct locations
    print "Deleting %s." % outputFilenameCSS
    try:
        os.remove("../../themes/%s/%s" % (theme, outputFilenameCSS))
    except:
        pass
    print "Moving new %s." % outputFilenameCSS
    shutil.move(outputFilenameCSS, "../../themes/%s" % theme)

def main(argv):
    try:
        parameter1 = argv[0]
    except:
        parameter1 = "ALL"

    try:
        if(argv[1] == "DOGIS"):
            parameter2 = True
        else:
            parameter2 = False
    except:
        parameter2 = True

    closure_warnings = True
    if "NOWARN" in argv:
        closure_warnings = False

    if parameter1 in ("ALL", "NOWARN"):
        dojs(warnings=closure_warnings)
        docss()
    else:
        if parameter1 == "CSS":
            docss()
        else:
            dojs(parameter2, warnings=closure_warnings)
            docss()
    print "Done."

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
