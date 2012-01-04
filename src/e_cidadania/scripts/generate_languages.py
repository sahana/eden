#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This script automates the creation of all the language catalogs for
e-cidadania project.
"""

import sys
import os
import subprocess
import argparse

__author__ = "Oscar Carballal"
__copyright__ = "Copyright 2011, Cidadania Sociedade Cooperativa Galega"
__credits__ = ["Oscar Carballal"]
__license__ = "GPLv3"
__version__ = "0.4"
__maintainer__ = "Oscar Carballal"
__email__ = "oscar.carballal@cidadania.coop"
__status__ = "Prototype"

class Language():

    """
    Language class.
    """
    def __init__(self):
        
        """
        Store all the applications and languages installed in the platfom
        """
        # Get current work directory and add it to sys.path so we can import
        # the project settings.
        self.cwd = os.getcwd().strip('scripts')
        sys.path.append(self.cwd)

        # Get the languages configured in settings.py and the installed
        # e-cidadania modules. If we can't get the settings module, abort execution.
        try:
            import settings
        except:
            sys.exit("\nCould not import the settings module. Aborting execution.\n\
            Probable cause: the script is not being executed from poject root.\n")

        self.applications = settings.ECIDADANIA_MODULES
        self.languages = settings.LANGUAGES
        self.apps = []

    def _iterator(self, command, type):

        """
        This method iterates over the applications and languages making
        what the command says.
        """
        for module in self.apps:
            os.chdir(self.cwd + '/apps/' + module)
            print '\n>> %s language catalog: %s' % (type, module)
            for lang in self.languages:
                a = subprocess.Popen(command + '%s' % (lang[0]), shell=True)
                subprocess.Popen.wait(a)

        print '\n>> %s site root language catalog.' % (type)
        os.chdir(self.cwd)
        for lang in self.languages:
            a = subprocess.Popen("django-admin.py makemessages -i 'apps/*' -l %s" % (lang[0]), shell=True)
            subprocess.Popen.wait(a)

            
    def make(self):
        
        """
        Generate the language catalogs for the application and site root
        """
        # Spit out the information
        print "\n>> Languages to generate:"
        for lang in self.languages:
            print ' - ' + lang[1]

        print "\n>> Installed applications:"
        for app in self.applications:
            self.got_it = app.split('.')[2]
            print ' - ' + self.got_it
            self.apps.append(self.got_it)
        self._iterator('django-admin.py makemessages -l ', 'Generating')
        self._iterator('django-admin.py makemessages -d djangojs -l ', 'Generating JavaScript')


    def compile(self):

        """
        """
        # Spit out the information
        print "\n>> Languages to generate:"
        for lang in self.languages:
            print ' - ' + lang[1]

        print "\n>> Installed applications:"
        for app in self.applications:
            self.got_it = app.split('.')[2]
            print ' - ' + self.got_it
            self.apps.append(self.got_it)

        for module in self.apps:
            os.chdir(self.cwd + '/apps/' + module)
            print '\n>> Compiling all messages for %s' % (module)
            a = subprocess.Popen('django-admin.py compilemessages ',
                                 shell=True)
            subprocess.Popen.wait(a)

        print '\n>> Compiling site root language catalogs'
        os.chdir(self.cwd)
        a = subprocess.Popen('django-admin.py compilemessages ', shell=True)
        subprocess.Popen.wait(a)


    def clean(self):

        """
        Removes the language installed catalogs in the platform, leaving the
        locale directories clean for new catalogs.
        """
        print '\n>> WARNING: This command will remove ALL the language \
catalogs, having to rebuild and translate them all.'
        raw_input('\n Continue? (Ctrl-C to quit)')
        for module in self.apps:
            os.chdir(self.cwd + '/apps/' + module)
            print '\n>> Cleaning language catalogs for %s' % (module)
            for lang in self.languages:
                a = subprocess.Popen('rm -rf locale/%s' % (lang[0]), shell=True)
                subprocess.Popen.wait(a)

        print '\n>> Cleaning site root language catalogs'
        os.chdir(self.cwd)
        for lang in self.languages:
            a = subprocess.Popen('rm -rf locale/%s' % (lang[0]), shell=True)
            subprocess.Popen.wait(a)

#print "\nPlease note that this script must be run from the project root or from \
#the scripts directory. If you run it from somewhere else it won't work."
#raw_input('\nPress any key to continue or Ctrl-C to exit...')

lang = Language()
parser = argparse.ArgumentParser(description='e-cidadania language catalog' \
    ' generator. This script manages all the .po and .mo files from templates,' \
    ' python code and javascript i18n (if used).')
subparser = parser.add_subparsers()
parser_make = subparser.add_parser('make', help='Create all the language' \
                                                ' catalogs for translation,'\
                                                ' including JavaScript.')
parser_make.set_defaults(func=lang.make)

parser_compile = subparser.add_parser('compile', help='Compile all the language' \
                                                      ' catalogs for use.')
parser_compile.set_defaults(func=lang.compile)

parser_clean = subparser.add_parser('clean', help='Delete all the language catalogs.' \
                                                  ' After this you will'\
                                                  ' have to rebuild the catalogs' \
                                                  ' and translate them.')
parser_clean.set_defaults(func=lang.clean)


args = parser.parse_args()
args.func()