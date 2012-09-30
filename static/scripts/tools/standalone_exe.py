#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Usage:
    Install py2exe: http://sourceforge.net/projects/py2exe/files/
    Copy script to the web2py directory
    c:\bin\python27\python standalone_exe.py py2exe
"""

from distutils.core import setup
import py2exe
from gluon.import_all import base_modules, contributed_modules
from glob import glob
import fnmatch
import os
import shutil
import sys

# Python base version
python_version = sys.version[:3]

# List of modules deprecated in python2.6 that are in the above set
py26_deprecated = ['mhlib', 'multifile', 'mimify', 'sets', 'MimeWriter']

if python_version == '2.6':
    base_modules += ['json', 'multiprocessing']
    base_modules = list(set(base_modules).difference(set(py26_deprecated)))

try:
	shutil.copytree('applications', 'dist/applications')
except:
	# This is entered when applications directory already exists in dist
	shutil.rmtree('dist/applications')
	shutil.copytree('applications', 'dist/applications')

try:
	shutil.copy('C:\Bin\Python26\DLLs\geos.dll', 'dist/')
	shutil.copy('C:\Bin\Python26\DLLs\libgeos-3-2-2.dll', 'dist/')
except:
	print "Copy geos.dll and libgeos-3-2-2.dll from Python26\DLLs into the dist directory"

if python_version == '2.6':
    # Python26 compatibility: http://www.py2exe.org/index.cgi/Tutorial#Step52
    try:
        shutil.copytree('C:\Bin\Microsoft.VC90.CRT', 'dist/')
    except:
        print "Copy Microsoft.VC90.CRT folder into the dist directory"

setup(
  console=['web2py.py'],
  windows=[{'script':'web2py.py',
    'dest_base':'web2py_no_console' # MUST NOT be just 'web2py' otherwise it overrides the standard web2py.exe
    }],
  data_files=[
        #'ABOUT',
        'LICENSE',
        'VERSION'
        ],
  options={'py2exe': {
    'packages': 
contributed_modules + ['lxml', 'serial', 'dateutil', 'reportlab', 'xlwt', 'shapely', 'PIL'],
    'includes': base_modules,
    }},
  )
