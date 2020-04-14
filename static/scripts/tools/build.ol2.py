import os
import shutil
import sys

import closure
import mergejs

closure.extra_params = "--warning_level QUIET"

PY2 = sys.version_info[0] == 2

# Open file in text mode, with Py3 to use encoding for unicode I/O
def openf(fn, mode):
    return open(fn, mode) if PY2 else open(fn, mode, encoding="utf-8")


def move_to(filename, path):
    """
        Replace the file at "path" location with the (newly built) file
        of the same name in the working directory
    """

    name = os.path.basename(filename)
    target = os.path.join(path, name)
    try:
        # Remove existing file
        os.remove(target)
    except:
        # Doesn't exist
        pass
    shutil.move(filename, path)

sourceDirectoryOpenLayers = "../gis/openlayers/lib"
configFilenameOpenLayers = "sahana.js.ol.cfg"
outputFilenameOpenLayers = "OpenLayers.js"
mergedOpenLayers = mergejs.run(sourceDirectoryOpenLayers,
                               None,
                               configFilenameOpenLayers)
# Suppress strict-mode errors
minimizedOpenLayers = closure.minimize(mergedOpenLayers,
                                       extra_params = "--strict_mode_input=false")
with openf(outputFilenameOpenLayers, "w") as outFile:
    #outFile.write(mergedOpenLayers)
    outFile.write(minimizedOpenLayers)

#os.system("terser OpenLayers.js -c -o OpenLayers.min.js")

move_to(outputFilenameOpenLayers, "../gis")
