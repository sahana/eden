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

print "\n>>>> e-cidadania language catalog generator 0.1 <<<<"
print "\nPlease note that this script must be run from the project root or from \
the scripts directory. If you run it from somewhere else it won't work."
raw_input('\nPress any key to continue or Ctrl-C to exit...')

class Language():

    """
    """
    def __init__(self):
        
        """
        """
        # Get current work directory and add it to sys.path so we can import
        # the project settings.
        self.cwd = os.getcwd().strip('scripts')
        sys.path.append(self.cwd)

        # Get the languages configured in settings.py and the installed
        # e-cidadania modules.
        import settings

        self.applications = settings.ECIDADANIA_MODULES
        self.languages = settings.LANGUAGES
        self.apps = []
        
        # Spit out the information
        print "\n>> Languages to generate:"
        for lang in self.languages:
            print ' - ' + lang[1]

        print "\n>> Installed applications:"
        for app in self.applications:
            self.got_it = app.split('.')[2]
            print ' - ' + self.got_it
            self.apps.append(self.got_it)

    def _iterator(self, command):

        """
        """
        for module in self.apps:
            os.chdir(self.cwd + '/apps/' + module)
            print '\n>> Generating language catalogs for %s' % (module)
            for lang in self.languages:
                a = subprocess.Popen(command + '%s' % (lang[0]), shell=True)
                subprocess.Popen.wait(a)

    def generate_catalog(self):
        
        """
        """
        self._iterator('django-admin.py makemessages -l ')

    def compile_catalog(self):

        """
        """
        for module in self.apps:
            os.chdir(self.cwd + '/apps/' + module)
            print '\n>> Compiling all messages for %s' % (module)
            a = subprocess.Popen('django-admin.py compilemessages ',
                                 shell=True)
            subprocess.Popen.wait(a)

lang = Language()

if sys.argv[1] == 'make':
    lang.generate_catalog()
elif sys.argv[1] == 'compile':
    lang.compile_catalog()
else:
    print '\nChoices are: make, compile'