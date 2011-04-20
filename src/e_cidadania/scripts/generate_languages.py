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

cwd = os.getcwd().strip('scripts')
sys.path.append(cwd)
print "\n>> e-cidadania language catalog generator 0.1"

# Put your language codes here. You can use the two letter code or the local
# code (es_ES, es_GL, en_US, en_GB, etc.)
languages = ['es', 'en', 'gl']


print "\n>> Languages to generate:"
for lang in languages:
    print lang

import settings

applications = settings.ECIDADANIA_MODULES

apps = []

print "\n>> Installed applications:"
for app in applications:
    got_it = app.split('.')[2]
    print got_it
    apps.append(got_it)

for i in apps:
    print i

def generate_catalog():
    for module in apps:
        os.chdir(cwd+'apps/'+module)
        os.Popen('django-admin makemessages', shell=True)
