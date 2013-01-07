"""
checkesc.py

Scans translations for unescaped characters and warns about them.
"""

import os
import io
import json
import re


USAGE = "{0} <path.to.translations>"
# This should get 99% escaping issues.
ESCAPE_RE = re.compile(r'\b[^\\][\\\'"][^\\]\b')

def _getline(lines, match):
    for i, line in enumerate(lines):
        line = unicode(line).encode('utf-8')
        if line[1:].startswith(match):
            return 2+i

def main(args):
    if len(args) < 2:
        print USAGE.format(os.path.relpath(args[0]))
        return
    else:
        for filename in os.listdir(args[1]):
            filepath = os.path.join(args[1], filename)

            if not filepath.endswith(".py"):
                continue

            with io.open(filepath, "r", encoding="utf-8") as file:
                # We strip away the first line here because Python can't
                # deal with encoding declarations in Unicode files.
                print "Checking: " + filename
                lines = file.readlines()[1:]
                code = "".join(lines)
                strings = eval(code)
                for key, val in strings.iteritems():
                    if ESCAPE_RE.search(val):
                        print "Potential encoding problem in {file}:{line}".format(
                            line=_getline(lines, key), file=filename)


if __name__ == "__main__":
    import sys
    main(sys.argv)
