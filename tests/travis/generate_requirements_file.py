#!/usr/bin/python
# usage - python generate_requirements.py [folder where the file should be generated] [list of requirements file]
# example - python tests/travis/generate_requirements_file.py tests/travis requirements.txt optional_requirements.txt

from sys import argv

# numpy - preinstalled
# matplotlib, lxml - installed from binaries
# pyrtf not working with pip

# packages not to be installed
exclude = ("numpy", "matplotlib", "lxml", "PyRTF", "PIL", "GDAL", "Shapely")

# the output requirements file
gen_req_file = open("%s/generated_requirements.txt" % argv[1], "w")

# iterate over all the requirements file
for req_file in argv[2:]:
    requirements = open(req_file).readlines()

    for line in requirements:
        line = line.strip()

        # comment in the file
        if line[0] == "#":
            continue

        found = False

        for item in exclude:
            if item.lower() in line.lower():
                found = True
                continue

        if found:
            continue

        gen_req_file.write("%s\n" % line)

gen_req_file.close()
