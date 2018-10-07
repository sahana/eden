#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Run as:
#   python web2py.py -S eden -M -R applications/eden/static/scripts/tools/build.sahana.py
# or:
#   python web2py.py -S eden -M -R applications/eden/static/scripts/tools/build.sahana.py -A <options>
#
# Options:
#   CSS    - CSS only (=do not build JavaScript)
#   DOGIS  - also build GIS JavaScript
#   NOWARN - suppress closure-compiler warnings (quiet mode)
#
# Built with code/inspiration from MapFish, OpenLayers & Michael Crute
#
try:
    theme = settings.get_theme()
except NameError:
    raise RuntimeError("Scripts needs to be run in the web2py environment in order to pick up which theme to build")

import re
import os
import shutil
import sys

# For JS
SCRIPTPATH = os.path.join(request.folder, "static", "scripts", "tools")
os.chdir(SCRIPTPATH)

sys.path.append("./")

import getopt
import jsmin
import mergejs

def info(msg):
    sys.stderr.write("%s\n" % msg)

# =============================================================================
# Optional builds
#
# Minify 3rd-party CSS?
CSS_FULL = False

# Minify 3rd-party JS?
JS_FULL = False

# Minify Vulnerability JS?
JS_VULNERABILITY = False

# =============================================================================
# Helper functions
#
def move_to(filename, path):
    """
        Replace the file at "path" location with the (newly built) file
        of the same name in the working directory
    """

    name = os.path.basename(filename)
    target = os.path.join(path, name)
    info("Replacing %s.\n" % target)
    try:
        # Remove existing file
        os.remove(target)
    except:
        # Doesn't exist
        pass
    shutil.move(filename, path)

# =============================================================================
# CSS Building
#

## Untested as libsass failing to run for me:
# For SCSS
#try:
#   import sass
#except ImportError:
#   info("Unable to import libsass: so if your theme includes SCSS sources, these won't be rebuilt")

def mergeCSS(inputFilenames, outputFilename):
    """ Merge (=concatenate) CSS files """

    with open(outputFilename, "w") as outFile:
        for inputFilename in inputFilenames:
            with open(inputFilename, "r") as inFile:
                outFile.write(inFile.read())

    return outputFilename

def csssub():
    """ CSS compression rules (regex, substitute) """

    # NB Order matters
    substitutions = (
        # Remove line breaks, tabs etc
        ("(\n|\r|\t|\f|\v)+", ""),
        # Kill double spaces
        ("(  )+", " "),
        # Remove last semicolon before }
        ("(; }|;})+", "}"),
        # Remove space before {
        ("({ )+", "{"),
        # Remove all comments
        ("/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/", ""),
        # Strip off the Charset
        ("@CHARSET .*;", ""),
        # Strip spaces before the {
        (" {", "{"),
        # Strip space after :
        (": ", ":"),
        # Strip space after ,
        (", ", ","),
        # Strip space after ;
        ("; ", ";"),
    )

    # Compile all Regex (only once per run)
    return [(re.compile(s[0]), s[1]) for s in substitutions]

# Initialize CSS patterns
csspatterns = csssub()

def cleanline(theLine):
    """ Compress a single line of CSS """

    cleaned = theLine
    for regex, sub in csspatterns:
        cleaned = regex.sub(sub, cleaned)
    return cleaned

def compressCSS(inputFilename, outputFilename):
    """ Compress a CSS file """

    with open(inputFilename, "r") as inFile:
        output = ""
        for line in inFile:
            output = output + cleanline(line)

    with open(outputFilename, "w") as outFile:
        outFile.write(cleanline(output))

def docss():
    """ Compresses the  CSS files """

    # -------------------------------------------------------------------------
    # Parse theme's css.cfg and build list of CSS files to merge
    #
    theme_styles = settings.get_theme_styles()
    info("Building theme %s" % theme_styles)

    css_cfg = os.path.join("..", "..", "..", "modules", "templates", theme_styles, "css.cfg")

    with open(css_cfg, "r") as f:
        css_paths = f.readlines()

    p = re.compile("(\n|\r|\t|\f|\v)+")

    listCSS = []
    for path in css_paths[:-1]:
        if path[0] == "#":
            # Comment line
            continue

        if path[:5] == "SCSS ":
            # Compile the SCSS first
            path = path[5:]

            filename = path.split("/")[-1].split(".")[0]
            sourcePath = os.path.join("..", "..", "..", "modules", "templates", theme_styles, "scss")
            sourceFilename = os.path.join(sourcePath, "%s.scss" % filename)

            with open(sourceFilename, "r") as sourceFile:
                source = sourceFile.read()

            os.chdir(sourcePath)
            outputText = sass.compile(source)
            os.chdir(SCRIPTPATH)

            with open(path, "w") as outputFile:
                outputFile.write(outputText)

        # Sanitize pathname
        path = p.sub("", path)
        listCSS.append("../../styles/%s" % path)

    # -------------------------------------------------------------------------
    # Build eden.min.css
    #
    outputFilenameCSS = "eden.min.css"

    info("Merging Core styles.")
    mergedCSS = mergeCSS(listCSS, outputFilenameCSS)

    info("Writing to %s." % outputFilenameCSS)
    compressCSS(mergedCSS, outputFilenameCSS)

    info("Deleting old %s." % outputFilenameCSS)
    try:
        os.remove("../../themes/%s/%s" % (theme_styles, outputFilenameCSS))
    except:
        pass

    if "/" in theme_styles:
        # Theme in sub-folder
        info("Adjusting relative URLs in %s." % outputFilenameCSS)
        with open(outputFilenameCSS, "r+") as outFile:
            css = outFile.readline()
            outFile.seek(0)
            outFile.write(css.replace("../../", "../../../"))

    info("Moving new %s." % outputFilenameCSS)
    shutil.move(outputFilenameCSS, "../../themes/%s/%s" % (theme_styles, outputFilenameCSS))

    # -------------------------------------------------------------------------
    # Optional CSS builds
    # - enable at the top when desired
    #
    if CSS_FULL:

        # Joyride, JSTree, Spectrum
        for filename in ("joyride",
                         "jstree",
                         "spectrum",
                         ):
            info("Merging %s styles." % filename)
            listCSS = ("../../styles/plugins/%s.css" % filename,)
            outputFilenameCSS = "%s.min.css" % filename
            mergedCSS = mergeCSS(listCSS, outputFilenameCSS)
            info("Writing to %s." % outputFilenameCSS)
            compressCSS(mergedCSS, outputFilenameCSS)
            # Move files to correct locations
            move_to(outputFilenameCSS, "../../styles/plugins")

        # Bootstrap
        info("Bootstrap CSS")
        listCSS = []
        for file in ["bootstrap.css",
                     "bootstrap-responsive.css",
                     "font-awesome.css",
                     #"bootstrap-multiselect.css",
                     ]:
            listCSS.append("../../styles/bootstrap/%s" % file)
        outputFilenameCSS = "bootstrap-combined.min.css"
        # Merge CSS files
        info("Merging Bootstrap styles.")
        mergedCSS = mergeCSS(listCSS, outputFilenameCSS)
        # Compress CSS files
        info("Writing to %s." % outputFilenameCSS)
        compressCSS(mergedCSS, outputFilenameCSS)
        # Move files to correct locations
        move_to(outputFilenameCSS, "../../styles/bootstrap")

        # Ext
        info("Ext Gray CSS")
        listCSS = []
        for file in ["ext-all-notheme.css",
                     "xtheme-gray.css",
                     ]:
            listCSS.append("../ext/resources/css/%s" % file)
        outputFilenameCSS = "ext-gray.min.css"
        info("Merging Ext styles.")
        mergedCSS = mergeCSS(listCSS, outputFilenameCSS)
        info("Writing to %s." % outputFilenameCSS)
        compressCSS(mergedCSS, outputFilenameCSS)
        move_to(outputFilenameCSS, "../ext/resources/css")

        info("Ext no-Theme CSS")
        outputFilenameCSS = "ext-notheme.min.css"
        info("Writing to %s." % outputFilenameCSS)
        compressCSS("../ext/resources/css/ext-all-notheme.css", outputFilenameCSS)
        move_to(outputFilenameCSS, "../ext/resources/css")

        info("Ext Themes CSS")
        outputFilenameCSS = "xtheme-ifrc.min.css"
        info("Writing to %s." % outputFilenameCSS)
        compressCSS("../../themes/IFRC/xtheme-ifrc.css", outputFilenameCSS)
        move_to(outputFilenameCSS, "../../themes/IFRC")

# =============================================================================
# JS Building
#
def minify_from_cfg(minimize, name, source_dir, cfg_name, out_filename, extra_params=None):
    """
        Merge+minify JS files from a JS config file (DRY helper for dojs)
    """

    info("Compressing %s" % name)

    # Merge + minify
    merged = mergejs.run(source_dir, None, cfg_name)
    if extra_params:
        try:
            # Assume closure
            minimized = minimize(merged, extra_params=extra_params)
        except:
            # No, not closure
            minimized = minimize(merged)
    else:
        minimized = minimize(merged)

    # Write minified file
    with open(out_filename, "w") as outFile:
        outFile.write(minimized)

    # Replace target file
    move_to(out_filename, "%s/S3" % source_dir)

def dojs(dogis = False, warnings = True):
    """ Minifies the JavaScript """

    # -------------------------------------------------------------------------
    # Determine which JS compressor to use
    #

    # Do we have local version of the Closure Compiler available?
    use_compressor = "jsmin" # Fallback
    try:
        import closure
        use_compressor = "closure"
        info("using local Closure Compiler")
    except Exception, E:
        info("No closure (%s)" % E)
        info("Download from http://dl.google.com/closure-compiler/compiler-latest.zip")
        try:
            import closure_ws
            use_compressor = "closure_ws"
            info("Using Closure via Web Service - limited to files < 1Mb!")
        except ImportError:
            info("No closure_ws")

    if use_compressor == "closure":
        if not warnings:
            closure.extra_params = "--warning_level QUIET"
        minimize = closure.minimize
    elif use_compressor == "closure_ws":
        minimize = closure_ws.minimize
    elif use_compressor == "jsmin":
        minimize = jsmin.jsmin

    # -------------------------------------------------------------------------
    # Build S3.min.js
    #
    sourceDirectory = ".."
    configFilename = "sahana.js.cfg"
    outputFilename = "S3.min.js"

    info("Merging Core libraries.")
    merged = mergejs.run(sourceDirectory, None, configFilename)

    info("Compressing - JS")
    minimized = minimize(merged)

    info("Adding license file.")
    minimized = open("license.txt").read() + minimized

    info("Writing to %s." % outputFilename)
    with open(outputFilename, "w") as outFile:
        outFile.write(minimized)

    # Remove old JS files
    info("Deleting %s." % outputFilename)
    try:
        os.remove("../S3/%s" % outputFilename)
    except:
        pass

    info("Moving new JS files")
    shutil.move(outputFilename, "../S3")

    # -------------------------------------------------------------------------
    # Build bootstrap
    #
    # Bootstrap
    # info("Compressing Bootstrap")
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

    # -------------------------------------------------------------------------
    # Build multi-component S3 scripts (=sahana.js.*.cfg files)
    # - configured as:
    #   (title, config-file, output-file, closure-extra-params)
    #
    s3_script_sets = (
        ("calendar",
         "sahana.js.calendar.cfg", "s3.ui.calendar.min.js", None),
        ("dataLists",
         "sahana.js.dataLists.cfg", "s3.dataLists.min.js", None),
        ("dataTables",
         "sahana.js.datatable.cfg", "s3.ui.datatable.min.js", None),
        ("dataTables (multi)",
         "sahana.js.dataTables_multi.cfg", "s3.dataTables.multi.min.js", None),
        ("groupedItems",
         "sahana.js.groupeditems.cfg", "s3.groupeditems.min.js", None),
        ("ImageCrop",
         "sahana.js.imageCrop.cfg", "s3.imagecrop.widget.min.js", None),
        ("JSTree",
         "sahana.js.jstree.cfg", "s3.jstree.min.js", None),
        ("Chat",
         "sahana.js.chat.cfg", "s3.chat.min.js", "--strict_mode_input=false"),
        ("Guided Tour",
         "sahana.js.guidedTour.cfg", "s3.guidedtour.min.js", None),
        )

    for name, cfg_name, out_filename, extra_params in s3_script_sets:
        minify_from_cfg(minimize,
                        name,
                        "..", # source_dir
                        cfg_name,
                        out_filename,
                        extra_params=extra_params,
                        )

    # -------------------------------------------------------------------------
    # Build single-component S3 scripts
    #
    for filename in ("cap",
                     "dc_answer",
                     "dc_question",
                     "dc_results",
                     "dvr",
                     "gis",
                     "gis.feature_crud",
                     "gis.fullscreen",
                     "gis.latlon",
                     "gis.loader",
                     "gis.pois",
                     "msg",
                     "popup",
                     "register_validation",
                     "shelter_inspection",
                     "sync",
                     "timeline",
                     "ui.addperson",
                     "ui.anonymize",
                     "ui.charts",
                     "ui.contacts",
                     "ui.dashboard",
                     "ui.embeddedcomponent",
                     "ui.locationselector",
                     "ui.permissions",
                     "ui.pivottable",
                     "ui.sitecheckin",
                     "ui.timeplot",
                     "work",
                     ):
        info("Compressing s3.%s.js" % filename)
        inputFilename = os.path.join("..", "S3", "s3.%s.js" % filename)
        outputFilename = "s3.%s.min.js" % filename
        with open(inputFilename, "r") as inFile:
            with open(outputFilename, "w") as outFile:
                outFile.write(minimize(inFile.read()))
        move_to(outputFilename, "../S3")

    # -------------------------------------------------------------------------
    # Optional JS builds
    # - enable at the top when desired
    #
    if JS_FULL:
        for filename in ("spectrum",
                         "tag-it",
                         ):
            info("Compressing %s.js" % filename)
            in_f = os.path.join("..", filename + ".js")
            out_f = os.path.join("..", filename + ".min.js")
            with open(in_f, "r") as inp:
                with open(out_f, "w") as out:
                    out.write(minimize(inp.read()))

    if JS_VULNERABILITY:
        # Vulnerability
        info("Compressing Vulnerability")
        sourceDirectory = "../.."
        configFilename = "sahana.js.vulnerability.cfg"
        outputFilename = "s3.vulnerability.min.js"
        merged = mergejs.run(sourceDirectory,
                             None,
                             configFilename)
        minimized = minimize(merged)
        with open(outputFilename, "w") as outFile:
            outFile.write(minimized)
        move_to(outputFilename, "../../themes/Vulnerability/js")

        info("Compressing Vulnerability GIS")
        sourceDirectory = "../.."
        configFilename = "sahana.js.vulnerability_gis.cfg"
        outputFilename = "OpenLayers.js"
        merged = mergejs.run(sourceDirectory,
                             None,
                             configFilename)
        minimized = minimize(merged)
        with open(outputFilename, "w") as outFile:
            outFile.write(minimized)
        move_to(outputFilename, "../../themes/Vulnerability/js")

        info("Compressing Vulnerability Datatables")
        sourceDirectory = "../.."
        configFilename = "sahana.js.vulnerability_datatables.cfg"
        outputFilename = "s3.dataTables.min.js"
        merged = mergejs.run(sourceDirectory,
                             None,
                             configFilename)
        minimized = minimize(merged)
        with open(outputFilename, "w") as outFile:
            outFile.write(minimized)
        move_to(outputFilename, "../../themes/Vulnerability/js")

    # -------------------------------------------------------------------------
    # GIS
    # - enable with command line option DOGIS
    #
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
        info("Merging OpenLayers libraries.")
        mergedOpenLayers = mergejs.run(sourceDirectoryOpenLayers,
                                       None,
                                       configFilenameOpenLayers)

        info("Merging MGRS libraries.")
        mergedMGRS = mergejs.run(sourceDirectoryMGRS,
                                 None,
                                 configFilenameMGRS)

        info("Merging GeoExt libraries.")
        mergedGeoExt = mergejs.run(sourceDirectoryGeoExt,
                                   None,
                                   configFilenameGeoExt)

        info("Merging gxp libraries.")
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
        if use_compressor == "closure":
            # Suppress strict-mode errors
            minimize_ = lambda stream: minimize(stream,
                                                extra_params="--strict_mode_input=false",
                                                )
        else:
            minimize_ = minimize

        info("Compressing - OpenLayers JS")
        if use_compressor == "closure_ws":
            # Limited to files < 1Mb!
            minimizedOpenLayers = jsmin.jsmin(mergedOpenLayers)
            #minimizedOpenLayers = jsmin.jsmin("%s\n%s" % (mergedOpenLayers,
            #                                              mergedOpenLayersExten))
        else:
            minimizedOpenLayers = minimize_(mergedOpenLayers)
            #minimizedOpenLayers = minimize_("%s\n%s" % (mergedOpenLayers,
            #                                           mergedOpenLayersExten))

        # OpenLayers extensions
        for filename in ("OWM.OpenLayers",
                         ):
            inputFilename = os.path.join("..", "gis", "%s.js" % filename)
            outputFilename = "%s.min.js" % filename

            with open(inputFilename, "r") as inFile:
                with open(outputFilename, "w") as outFile:
                    outFile.write(minimize_(inFile.read()))
            move_to(outputFilename, "../gis")

        info("Compressing - MGRS JS")
        minimizedMGRS = minimize_(mergedMGRS)

        info("Compressing - GeoExt JS")
        minimizedGeoExt = minimize_("%s\n%s" % (mergedGeoExt,
                                                #mergedGeoExtux,
                                                mergedGxpMin))

        # GeoNamesSearchCombo
        inputFilename = os.path.join("..", "gis", "GeoExt", "ux", "GeoNamesSearchCombo.js")
        outputFilename = "GeoNamesSearchCombo.min.js"
        with open(inputFilename, "r") as inFile:
            with open(outputFilename, "w") as outFile:
                outFile.write(minimize_(inFile.read()))
        move_to(outputFilename, "../gis/GeoExt/ux")

        info("Compressing - gxp JS")
        minimizedGxp = minimize_(mergedGxpFull)
        minimizedGxp2 = minimize_(mergedGxp2)

        for filename in ("WMSGetFeatureInfo",
                         ):
            inputFilename = os.path.join("..", "gis", "gxp", "plugins", "%s.js" % filename)
            outputFilename = "%s.min.js" % filename
            with open(inputFilename, "r") as inFile:
                with open(outputFilename, "w") as outFile:
                    outFile.write(minimize_(inFile.read()))
            move_to(outputFilename, "../gis/gxp/plugins")

        for filename in (#"GoogleEarthPanel",
                         "GoogleStreetViewPanel",
                         ):
            inputFilename = os.path.join("..", "gis", "gxp", "widgets", "%s.js" % filename)
            outputFilename = "%s.min.js" % filename
            with open(inputFilename, "r") as inFile:
                with open(outputFilename, "w") as outFile:
                    outFile.write(minimize_(inFile.read()))
            move_to(outputFilename, "../gis/gxp/widgets")

        # Add license
        #minimizedGIS = open("license.gis.txt").read() + minimizedGIS

        # Print to output files
        info("Writing to %s." % outputFilenameOpenLayers)
        with open(outputFilenameOpenLayers, "w") as outFile:
            outFile.write(minimizedOpenLayers)
        info("Moving new OpenLayers JS files")
        move_to(outputFilenameOpenLayers, "../gis")

        info("Writing to %s." % outputFilenameMGRS)
        with open(outputFilenameMGRS, "w") as outFile:
            outFile.write(minimizedMGRS)
        info("Moving new MGRS JS files")
        move_to(outputFilenameMGRS, "../gis")

        info("Writing to %s." % outputFilenameGeoExt)
        with open(outputFilenameGeoExt, "w") as outFile:
            outFile.write(minimizedGeoExt)
        info("Moving new GeoExt JS files")
        move_to(outputFilenameGeoExt, "../gis")

        info("Writing to %s." % outputFilenameGxp)
        with open(outputFilenameGxp, "w") as outFile:
            outFile.write(minimizedGxp)
        info("Moving new gxp JS files")
        move_to(outputFilenameGxp, "../gis")

        info("Writing to %s." % outputFilenameGxp2)
        with open(outputFilenameGxp2, "w") as outFile:
            outFile.write(minimizedGxp2)
        info("Moving new gxp2 JS files")
        move_to(outputFilenameGxp2, "../gis")

# =============================================================================
# Main script
#
def main(argv):

    # Rebuild GIS JS?
    dogis = "DOGIS" in argv

    # Suppress closure warnings?
    warnings = "NOWARN" not in argv

    if "CSS" in argv:
        # Build CSS only
        docss()
    else:
        dojs(dogis=dogis, warnings=warnings)
        docss()

    info("Done.")

if __name__ == "__main__":

    sys.exit(main(sys.argv[1:]))

# END =========================================================================
