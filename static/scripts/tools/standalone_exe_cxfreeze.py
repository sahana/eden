#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Usage:
    Install cx_Freeze: http://cx-freeze.sourceforge.net/
    Copy script to the web2py directory
    c:\Python27\python standalone_exe_cxfreeze.py build_exe
"""
from cx_Freeze import setup, Executable
from gluon.import_all import base_modules, contributed_modules
from gluon.fileutils import readlines_file
from glob import glob
import fnmatch
import os
import shutil
import sys
import re

#read web2py version from VERSION file
web2py_version_line = readlines_file('VERSION')[0]
#use regular expression to get just the version number
v_re = re.compile('[0-9]+\.[0-9]+\.[0-9]+')
web2py_version = v_re.search(web2py_version_line).group(0)

try:
    shutil.copy('C:\Python27\DLLs\geos.dll', '.')
    shutil.copy('C:\Python27\DLLs\geos_c.dll', '.')
except:
    print "Copy geos.dll and geos_c.dll from Python27\DLLs into the web2py directory"

shutil.copy(os.path.join('applications', 'eden', 'static', 'favicon.ico'), '.')

base = None

if sys.platform == 'win32':
    base = "Win32GUI"

base_modules.remove('macpath')
buildOptions = dict(
        compressed = True,
        excludes = ["macpath", "PyQt4"],
    	includes = base_modules,
  	    include_files=[
            'applications',
            #'ABOUT',
            'LICENSE',
            'VERSION',
            #'logging.example.conf',
            #'options_std.py',
            #'app.example.yaml',
            #'queue.example.yaml',
            'geos.dll',
            'geos_c.dll'
            ],
        packages = contributed_modules + ['PIL', 'lxml', 'dateutil', 'reportlab', 'xlrd', 'xlwt', 'shapely'], #, 'pytz', 'tweepy', 'serial'
        )

setup(
        name = "Sahana",
        version=web2py_version, # @ToDo: Use Eden version
        author="Sahana Software Foundation",
        description="Sahana Eden Humanitarian Management Platform",
        license = "MIT",
        options = dict(build_exe = buildOptions),
        executables = [Executable("web2py.py",
                                    base=base,
                                    compress = True,
                                    icon = "favicon.ico",
                                    targetName="sahana.exe",
                                    copyDependentFiles = True)],
        )
