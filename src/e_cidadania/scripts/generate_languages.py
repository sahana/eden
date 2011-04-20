# -*- coding: utf-8 -*-
#
# Copyright (c) 2010 Cidadanía Coop.
# Written by: Oscar Carballal Prego <info@oscarcp.com>
#
# This file is part of e-cidadania.
#
# e-cidadania is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# e-cidadania is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with e-cidadania. If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import subprocess

print "\nPlease note that this script must be run from the project root or from \
the scripts directory. If you run it from somewhere else it won't work."

raw_input('\nPress any key to continue or Ctrl-C to exit...')

cwd = os.getcwd().strip('scripts')
sys.path.append(cwd)
print "\n>>>> e-cidadania language catalog generator 0.1 <<<<"

import settings

applications = settings.ECIDADANIA_MODULES
languages = settings.LANGUAGES
apps = []

print "\n>> Languages to generate:"
for lang in languages:
    print ' - ' + lang[1]

print "\n>> Installed applications:"
for app in applications:
    got_it = app.split('.')[2]
    print ' - ' + got_it
    apps.append(got_it)

def generate_catalog():
    for module in apps:
        os.chdir(cwd+'/apps/'+module)
        print '\n>> Generating language catalogs for %s' % (module)
        for lang in languages:
            a = subprocess.Popen('django-admin makemessages -l %s' % (lang[0]), shell=True)
            subprocess.Popen.wait(a)

generate_catalog()
