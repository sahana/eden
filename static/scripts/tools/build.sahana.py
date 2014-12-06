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

## Untested as libsass failing to run for me:
# For SCSS
#try:
#    import sass
#except:
#    print "Unable to import libsass: so if your theme includes SCSS sources, these won't be rebuilt"

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

    # Bootstrap
    # print "Compressing Bootstrap"
    # sourceDirectoryBootstrap = ".."
    # configFilenameBootstrap = "sahana.js.bootstrap.cfg"
    # outputFilenameBootstrap = "bootstrap.min.js"
    # mergedBootstrap = mergejs.run(sourceDirectoryBootstrap,
                                  # None,
                                  # configFilenameBootstrap)
    # minimizedBootstrap = minimize(mergedBootstrap)
    # open(outputFilenameBootstrap, "w").write(minimizedBootstrap)
    # try:
        # os.remove("../%s" % outputFilenameBootstrap)
    # except:
        # pass
    # shutil.move(outputFilenameBootstrap, "..")

    # dataLists
    print "Compressing dataLists"
    sourceDirectory = ".."
    configFilename = "sahana.js.dataLists.cfg"
    outputFilename = "s3.dataLists.min.js"
    merged = mergejs.run(sourceDirectory,
                         None,
                         configFilename)
    minimized = minimize(merged)
    open(outputFilename, "w").write(minimized)
    try:
        os.remove("../S3/%s" % outputFilename)
    except:
        pass
    shutil.move(outputFilename, "../S3")

    # dataTables
    print "Compressing dataTables"
    sourceDirectory = ".."
    configFilename = "sahana.js.dataTables.cfg"
    outputFilename = "s3.dataTables.min.js"
    merged = mergejs.run(sourceDirectory,
                         None,
                         configFilename)
    minimized = minimize(merged)
    open(outputFilename, "w").write(minimized)
    try:
        os.remove("../S3/%s" % outputFilename)
    except:
        pass
    shutil.move(outputFilename, "../S3")

    configFilename = "sahana.js.dataTables_multi.cfg"
    outputFilename = "s3.dataTables.multi.min.js"
    merged = mergejs.run(sourceDirectory,
                                   None,
                                   configFilename)
    minimized = minimize(merged)
    open(outputFilename, "w").write(minimized)
    try:
        os.remove("../S3/%s" % outputFilename)
    except:
        pass
    shutil.move(outputFilename, "../S3")

    # pivotTables
    print "Compressing pivotTables"
    sourceDirectory = ".."
    configFilename = "sahana.js.pivotTables.cfg"
    outputFilename = "s3.pivotTables.min.js"
    merged = mergejs.run(sourceDirectory,
                         None,
                         configFilename)
    minimized = minimize(merged)
    open(outputFilename, "w").write(minimized)
    try:
        os.remove("../S3/%s" % outputFilename)
    except:
        pass
    shutil.move(outputFilename, "../S3")

    # timeplot
    print "Compressing timeplot"
    sourceDirectory = ".."
    configFilename = "sahana.js.timeplot.cfg"
    outputFilename = "s3.timeplot.min.js"
    merged = mergejs.run(sourceDirectory,
                         None,
                         configFilename)
    minimized = minimize(merged)
    open(outputFilename, "w").write(minimized)
    try:
        os.remove("../S3/%s" % outputFilename)
    except:
        pass
    shutil.move(outputFilename, "../S3")

    # ImageCrop
    print "Compressing ImageCrop"
    sourceDirectory = ".."
    configFilename = "sahana.js.imageCrop.cfg"
    outputFilename = "s3.imagecrop.widget.min.js"
    merged = mergejs.run(sourceDirectory,
                         None,
                         configFilename)
    minimized = minimize(merged)
    open(outputFilename, "w").write(minimized)
    try:
        os.remove("../S3/%s" % outputFilename)
    except:
        pass
    shutil.move(outputFilename, "../S3")

    # JSTree
    print "Compressing JSTree"
    sourceDirectory = ".."
    configFilename = "sahana.js.jstree.cfg"
    outputFilename = "s3.jstree.min.js"
    merged = mergejs.run(sourceDirectory,
                         None,
                         configFilename)
    minimized = minimize(merged)
    open(outputFilename, "w").write(minimized)
    try:
        os.remove("../S3/%s" % outputFilename)
    except:
        pass
    shutil.move(outputFilename, "../S3")

    # Chat
    print "Compressing Chat"
    sourceDirectory = ".."
    configFilename = "sahana.js.chat.cfg"
    outputFilename = "s3.chat.min.js"
    merged = mergejs.run(sourceDirectory,
                         None,
                         configFilename)
    minimized = minimize(merged)
    open(outputFilename, "w").write(minimized)
    try:
        os.remove("../S3/%s" % outputFilename)
    except:
        pass
    shutil.move(outputFilename, "../S3")

    # Guided Tour
    print "Compressing Guided Tour"
    sourceDirectory = ".."
    configFilename = "sahana.js.guidedTour.cfg"
    outputFilename = "s3.guidedtour.min.js"
    merged = mergejs.run(sourceDirectory,
                         None,
                         configFilename)
    minimized = minimize(merged)
    open(outputFilename, "w").write(minimized)
    try:
        os.remove("../S3/%s" % outputFilename)
    except:
        pass
    shutil.move(outputFilename, "../S3")

    # Single scripts
    for filename in ("add_person",
                     "cap",
                     "contacts",
                     "embed_component",
                     "gis",
                     "gis.feature_crud",
                     "gis.fullscreen",
                     "gis.latlon",
                     "gis.loader",
                     "gis.pois",
                     "locationselector.widget",
                     "ui.locationselector",
                     "msg",
                     "popup",
                     "register_validation",
                     "select_person",
                     "timeline",
                     ):
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

    # Enable when needed
    full = False
    if full:
        for filename in ("spectrum",
                         "tag-it",
                         ):
            print "Compressing %s.js" % filename
            in_f = os.path.join("..", filename + ".js")
            out_f = os.path.join("..", filename + ".min.js")
            with open(in_f, "r") as inp:
                with open(out_f, "w") as out:
                    out.write(minimize(inp.read()))

        # Vulnerability
        print "Compressing Vulnerability"
        sourceDirectory = "../.."
        configFilename = "sahana.js.vulnerability.cfg"
        outputFilename = "s3.vulnerability.min.js"
        merged = mergejs.run(sourceDirectory,
                             None,
                             configFilename)
        minimized = minimize(merged)
        open(outputFilename, "w").write(minimized)
        try:
            os.remove("../../themes/Vulnerability/js/%s" % outputFilename)
        except:
            pass
        shutil.move(outputFilename, "../../themes/Vulnerability/js")
        print "Compressing Vulnerability GIS"
        sourceDirectory = "../.."
        configFilename = "sahana.js.vulnerability_gis.cfg"
        outputFilename = "OpenLayers.js"
        merged = mergejs.run(sourceDirectory,
                             None,
                             configFilename)
        minimized = minimize(merged)
        open(outputFilename, "w").write(minimized)
        try:
            os.remove("../../themes/Vulnerability/js/%s" % outputFilename)
        except:
            pass
        shutil.move(outputFilename, "../../themes/Vulnerability/js")

    if dogis:
        sourceDirectoryOpenLayers = "../gis/openlayers/lib"
        sourceDirectoryMGRS = "../gis"
        sourceDirectoryGeoExt = "../gis/GeoExt/lib"
        sourceDirectoryGxp = "../gis/gxp"
        configFilenameOpenLayers = "sahana.js.ol.cfg"
        configFilenameMGRS = "sahana.js.mgrs.cfg"
        configFilenameGeoExt = "sahana.js.geoext.cfg"
        configFilenameGxpMin = "sahana.js.gxp.cfg"
        configFilenameGxp2 = "sahana.js.gxp2.cfg"
        configFilenameGxpFull = "sahana.js.gxpfull.cfg"
        outputFilenameOpenLayers = "OpenLayers.js"
        outputFilenameMGRS = "MGRS.min.js"
        outputFilenameGeoExt = "GeoExt.js"
        outputFilenameGxp = "gxp.js"
        outputFilenameGxp2 = "gxp_upload.js"

        # Merge GIS JS Files
        print "Merging OpenLayers libraries."
        mergedOpenLayers = mergejs.run(sourceDirectoryOpenLayers,
                                       None,
                                       configFilenameOpenLayers)

        print "Merging MGRS libraries."
        mergedMGRS = mergejs.run(sourceDirectoryMGRS,
                                 None,
                                 configFilenameMGRS)

        print "Merging GeoExt libraries."
        mergedGeoExt = mergejs.run(sourceDirectoryGeoExt,
                                   None,
                                   configFilenameGeoExt)

        print "Merging gxp libraries."
        mergedGxpMin = mergejs.run(sourceDirectoryGxp,
                                   None,
                                   configFilenameGxpMin)
        mergedGxp2 = mergejs.run(sourceDirectoryGxp,
                                 None,
                                 configFilenameGxp2)
        mergedGxpFull = mergejs.run(sourceDirectoryGxp,
                                    None,
                                    configFilenameGxpFull)

        # Compress JS files
        print "Compressing - OpenLayers JS"
        if use_compressor == "closure_ws":
            # Limited to files < 1Mb!
            minimizedOpenLayers = jsmin.jsmin(mergedOpenLayers)
            #minimizedOpenLayers = jsmin.jsmin("%s\n%s" % (mergedOpenLayers,
            #                                              mergedOpenLayersExten))
        else:
            minimizedOpenLayers = minimize(mergedOpenLayers)
            #minimizedOpenLayers = minimize("%s\n%s" % (mergedOpenLayers,
            #                                           mergedOpenLayersExten))

        # OpenLayers extensions
        for filename in ["OWM.OpenLayers",
                         ]:
            inputFilename = os.path.join("..", "gis", "%s.js" % filename)
            outputFilename = "%s.min.js" % filename
            input = open(inputFilename, "r").read()
            minimized = minimize(input)
            open(outputFilename, "w").write(minimized)
            try:
                os.remove("../gis/%s" % outputFilename)
            except:
                pass
            shutil.move(outputFilename, "../gis")

        print "Compressing - MGRS JS"
        minimizedMGRS = minimize(mergedMGRS)

        print "Compressing - GeoExt JS"
        minimizedGeoExt = minimize("%s\n%s" % (mergedGeoExt,
                                               #mergedGeoExtux,
                                               mergedGxpMin))

        # GeoNamesSearchCombo
        inputFilename = os.path.join("..", "gis", "GeoExt", "ux", "GeoNamesSearchCombo.js")
        outputFilename = "GeoNamesSearchCombo.min.js"
        input = open(inputFilename, "r").read()
        minimized = minimize(input)
        open(outputFilename, "w").write(minimized)
        try:
            os.remove("../gis/GeoExt/ux/%s" % outputFilename)
        except:
            pass
        shutil.move(outputFilename, "../gis/GeoExt/ux")

        print "Compressing - gxp JS"
        minimizedGxp = minimize(mergedGxpFull)
        minimizedGxp2 = minimize(mergedGxp2)

        for filename in ("WMSGetFeatureInfo",
                         ):
            inputFilename = os.path.join("..", "gis", "gxp", "plugins", "%s.js" % filename)
            outputFilename = "%s.min.js" % filename
            input = open(inputFilename, "r").read()
            minimized = minimize(input)
            open(outputFilename, "w").write(minimized)
            try:
                os.remove("../gis/gxp/plugins/%s" % outputFilename)
            except:
                pass
            shutil.move(outputFilename, "../gis/gxp/plugins")

        for filename in ("GoogleEarthPanel",
                         "GoogleStreetViewPanel",
                         ):
            inputFilename = os.path.join("..", "gis", "gxp", "widgets", "%s.js" % filename)
            outputFilename = "%s.min.js" % filename
            input = open(inputFilename, "r").read()
            minimized = minimize(input)
            open(outputFilename, "w").write(minimized)
            try:
                os.remove("../gis/gxp/widgets/%s" % outputFilename)
            except:
                pass
            shutil.move(outputFilename, "../gis/gxp/widgets")

        # Add license
        #minimizedGIS = open("license.gis.txt").read() + minimizedGIS

        # Print to output files
        print "Writing to %s." % outputFilenameOpenLayers
        open(outputFilenameOpenLayers, "w").write(minimizedOpenLayers)

        print "Writing to %s." % outputFilenameMGRS
        open(outputFilenameMGRS, "w").write(minimizedMGRS)

        print "Writing to %s." % outputFilenameGeoExt
        open(outputFilenameGeoExt, "w").write(minimizedGeoExt)

        print "Writing to %s." % outputFilenameGxp
        open(outputFilenameGxp, "w").write(minimizedGxp)

        print "Writing to %s." % outputFilenameGxp2
        open(outputFilenameGxp2, "w").write(minimizedGxp2)

        # Move new JS files
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

        print "Deleting %s." % outputFilenameGxp2
        try:
            os.remove("../gis/%s" % outputFilenameGxp2)
        except:
            pass
        print "Moving new gxp2 JS files"
        shutil.move(outputFilenameGxp2, "../gis")

def docss():
    """ Compresses the  CSS files """

    # Theme
    theme = settings.get_theme()
    print "Using theme %s" % theme
    css_cfg = os.path.join("..", "..", "..", "private", "templates", theme, "css.cfg")
    f = open(css_cfg, "r")
    files = f.readlines()
    f.close()
    listCSS = []
    for file in files[:-1]:
        if file[0] != "#":
            # Real line, not a comment
            if file[:5] == "SCSS ":
                # Compile the SCSS first
                file = file[5:]
                filename = file.split("/")[-1].split(".")[0]
                sourcePath = os.path.join("..", "..", "..", "private", "templates", theme, "scss")
                sourceFilename = os.path.join(sourcePath, "%s.scss" % filename)
                sourceFile = open(sourceFilename, "r")
                source = sourceFile.read()
                sourceFile.close()
                os.chdir(sourcePath)
                outputText = sass.compile(source)
                os.chdir(SCRIPTPATH)
                outputFile = open(file, "w")
                outputFile.write(outputText)
                outputFile.close()

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

    # Enable when needed
    full = False
    if full:
        for filename in ("joyride",
                         "jstree",
                         "spectrum",
                         ):
            print "Merging %s styles." % filename
            listCSS = ("../../styles/plugins/%s.css" % filename,)
            outputFilenameCSS = "%s.min.css" % filename
            mergedCSS = mergeCSS(listCSS, outputFilenameCSS)
            print "Writing to %s." % outputFilenameCSS
            compressCSS(mergedCSS, outputFilenameCSS)
            # Move files to correct locations
            print "Deleting %s." % outputFilenameCSS
            try:
                os.remove("../../styles/plugins/%s" % outputFilenameCSS)
            except:
                pass
            print "Moving new %s." % outputFilenameCSS
            shutil.move(outputFilenameCSS, "../../styles/plugins")

        # Bootstrap
        print "Bootstrap CSS"
        listCSS = []
        for file in ["bootstrap.css",
                     "bootstrap-responsive.css",
                     "font-awesome.css",
                     #"bootstrap-multiselect.css",
                     ]:
            listCSS.append("../../styles/bootstrap/%s" % file)

        outputFilenameCSS = "bootstrap-combined.min.css"

        # Merge CSS files
        print "Merging Bootstrap styles."
        mergedCSS = mergeCSS(listCSS, outputFilenameCSS)

        # Compress CSS files
        print "Writing to %s." % outputFilenameCSS
        compressCSS(mergedCSS, outputFilenameCSS)

        # Move files to correct locations
        print "Deleting %s." % outputFilenameCSS
        try:
            os.remove("../../styles/bootstrap/%s" % outputFilenameCSS)
        except:
            pass
        print "Moving new %s." % outputFilenameCSS
        shutil.move(outputFilenameCSS, "../../styles/bootstrap")

        # Ext
        print "Ext Gray CSS"
        listCSS = []
        for file in ["ext-all-notheme.css",
                     "xtheme-gray.css",
                     ]:
            listCSS.append("../ext/resources/css/%s" % file)

        outputFilenameCSS = "ext-gray.min.css"

        # Merge CSS files
        print "Merging Ext styles."
        mergedCSS = mergeCSS(listCSS, outputFilenameCSS)

        # Compress CSS file
        print "Writing to %s." % outputFilenameCSS
        compressCSS(mergedCSS, outputFilenameCSS)

        # Move files to correct locations
        print "Deleting %s." % outputFilenameCSS
        try:
            os.remove("../ext/resources/css/%s" % outputFilenameCSS)
        except:
            pass
        print "Moving new %s." % outputFilenameCSS
        shutil.move(outputFilenameCSS, "../ext/resources/css")

        print "Ext no-Theme CSS"
        outputFilenameCSS = "ext-notheme.min.css"

        # Compress CSS file
        print "Writing to %s." % outputFilenameCSS
        compressCSS("../ext/resources/css/ext-all-notheme.css", outputFilenameCSS)

        # Move files to correct locations
        print "Deleting %s." % outputFilenameCSS
        try:
            os.remove("../ext/resources/css/%s" % outputFilenameCSS)
        except:
            pass
        print "Moving new %s." % outputFilenameCSS
        shutil.move(outputFilenameCSS, "../ext/resources/css")

        print "Ext Themes CSS"
        outputFilenameCSS = "xtheme-ifrc.min.css"

        # Compress CSS file
        print "Writing to %s." % outputFilenameCSS
        compressCSS("../../themes/IFRC/xtheme-ifrc.css", outputFilenameCSS)

        # Move files to correct locations
        print "Deleting %s." % outputFilenameCSS
        try:
            os.remove("../../themes/IFRC/%s" % outputFilenameCSS)
        except:
            pass
        print "Moving new %s." % outputFilenameCSS
        shutil.move(outputFilenameCSS, "../../themes/IFRC")

def main(argv):
    if len(argv) > 0:
        parameter1 = argv[0]
    else:
        parameter1 = "ALL"

    if len(argv) > 1:
        if(argv[1] == "DOGIS"):
            parameter2 = True
        else:
            parameter2 = False
    else:
        parameter2 = True

    closure_warnings = True
    if "NOWARN" in argv:
        closure_warnings = False

    if parameter1 in ("ALL", "NOWARN"):
        dojs(warnings=closure_warnings)
        docss()
    else:
        if parameter1 in ("CSS", "css"):
            docss()
        else:
            dojs(parameter2, warnings=closure_warnings)
            docss()
    print "Done."

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
