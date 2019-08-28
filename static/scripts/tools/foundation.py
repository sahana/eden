import os
import shutil

import sys

PY2 = sys.version_info[0] == 2

# Open file in text mode, with Py3 to use encoding for unicode I/O
def openf(fn, mode):
    return open(fn, mode) if PY2 else open(fn, mode, encoding="utf-8")

def info(msg):
    sys.stderr.write("%s\n" % msg)

import mergejs

import closure
closure.extra_params = "--warning_level QUIET"
minimize = closure.minimize

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

merged = mergejs.run("..", None, "foundation.cfg")
minimized = minimize(merged)
# Write minified file
with openf("foundation.min.js", "w") as outFile:
    outFile.write(minimized)
# Replace target file
move_to("foundation.min.js", "../foundation")
