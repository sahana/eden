#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" This script download the latest git version of e-cidadania, compiles
the documentation and places it in the documentation website
"""

import sys
import os
import subprocess
import argparse


__author__ = "Oscar Carballal Prego"
__license__ = "GPLv3"
__version__ = "0.2"
__email__ = "oscar.carballal@cidadania.coop"
__status__ = "Stable/Production"

class Documents():

    """
    Document class.
    """
    def __init__(self):

        """
        Declare variables.
        """
        self.cwd = os.getcwd()
        self.langs = ["es", "en", "gl"]
        self.formats = ["html", "latex", "latexpdf"]

        # We don't include cidadania's server repository because it
        # needs authentication and some specific settings.
        self.repos = [
            "git://github.com/cidadania/e-cidadania.git",
            "git://github.com/oscarcp/e-cidadania.git",
            "git://gitorious.org/e-cidadania/mainline.git",
            "git://repo.or.cz/e_cidadania.git",
        ]

    def download_code(self, branch='master'):

        """
        Download the latest code from the e-cidadania repositories. It the
        clone fails it will try with the next repository until it finds
        a working one.
        """
        i = 0
        print "\n >> Getting e-cidadania codebase from %s..." % self.repos[i].split('/')[2]
        print "DEBUG: BRANCH=%s" % branch
        done = False
        while not done:
            if i <= (len(self.repos) - 1):
                try:
                    get_code = subprocess.check_call('git clone -b ' + branch + ' ' + self.repos[i] + ' ../ecidadania > /dev/null 2>&1', shell=True)
                    done = True
                except:
                    print " -- Couldn't get the code from %s" % self.repos[i].split('/')[2]
                    i += 1
            else:
                import shutil
                print "\n EE Couldn't get the e-cidadania codebase. This can be caused by an old copy of the codebase."
                print " -- Trying to delete the old codebase..."
                try:
                    os.chdir('../')
                    shutil.rmtree('ecidadania/')
                    print " -- Code succesfully deleted. Please run the application again.\n"
                    os.chdir('scripts/')
                except:
                    print " -- There was some error trying to delete the old codebase. Exiting.\n"
                sys.exit()

    def compile_docs(self):

        """
        Compile all the documentation and languages at once.
        """
        os.chdir(self.cwd + '/../ecidadania/docs/')
        sys.stdout.write("\n >> Compiling documentation... ")
        sys.stdout.flush()

        i = 0
        done = False
        while not done:
            if i < (len(self.formats) - 1):
                try:
                    sys.stdout.write('(%s) ' % self.formats[i])
                    sys.stdout.flush()
                    gen_docs = subprocess.check_call('make ' + self.formats[i] + ' > /dev/null 2>&1', shell=True)
                    if gen_docs == 0:
                        i += 1
                except:
                    print " -- Couldn't compile the %s documentation." % self.formats[i]
                    i += 1
            elif i == (len(self.formats) - 1):
                try:
                    sys.stdout.write('(%s) ' % self.formats[i])
                    sys.stdout.flush()
                    gen_docs = subprocess.check_call('make ' + self.formats[i] + ' > /dev/null 2>&1', shell=True)
                    if gen_docs == 0:
                        i += 1
                        done = True
                except:
                    print " -- Couldn't compile the %s documentation." % self.formats[i]
                    i += 1
            else:
                sys.exit("\n EE Couldn't generate documentation. Exiting.\n")
        print "\n"

    def pack_latex(self):

        """
        Package the LaTeX documentation into a tar.gz
        """
        print " >> Packaging the LaTeX files..."
        import tarfile
        
        os.chdir(os.getcwd() + '/build/latex/')
        i = 0
        while i <= (len(self.langs) - 1):
            tar = tarfile.open(os.getcwd() + "/../../%s/latest-%s.tar.gz" % (self.langs[i], self.langs[i]), "w:gz")
            tar.add(self.langs[i])
            tar.close()
            i += 1
            

    def copy_docs(self):

        """
        Copy the generated documentation into their respective directories.
        """
        os.chdir("../../")

        c = 0
        while c <= (len(self.formats) - 1):
            print " >> Copying the %s documentation..." % self.formats[c]
            sys.stdout.write(" >> done ")
            sys.stdout.flush()
            
            i = 0
            while i <= (len(self.langs) - 1):
                if self.formats[c] == 'latexpdf':
                    try:
                        copy_latexpdf = subprocess.check_call('cp -R build/latex/' + self.langs[i] + '/e-cidadania.pdf ../../' + self.langs[i] + '/latest-' + self.langs[i] + '.pdf', shell=True)
                    except:
                        print " -- Couldn't copy the " + self.langs[i] + " documentation."
                        pass
                    sys.stdout.write("(%s) " % self.langs[i])
                    sys.stdout.flush()
                    i += 1
                elif self.formats[c] == 'html':
                    try:
                        copy_html = subprocess.check_call('cp -R build/' + self.formats[c] + '/' + self.langs[i] + '/* ../../' + self.langs[i] + '/latest', shell=True)
                    except:
                        print " -- Couldn't copy the " + self.langs[i] + " documentation."
                        pass
                    sys.stdout.write("(%s) " % self.langs[i])
                    sys.stdout.flush()
                    i += 1
                elif self.formats[c] == 'latex':
                    try:
                        copy_latex = subprocess.check_call('cp -R ' + self.langs[i] + '/latest-' + self.langs[i] + '.tar.gz' + ' ../../' + self.langs[i], shell=True)
                    except:
                        print " -- Couldn't copy the " + self.langs[i] + " documentation."
                        print " EE Couldn't copy one or all the documentation! Exiting."
                        sys.exit(1)
                    sys.stdout.write("(%s) " % self.langs[i])
                    sys.stdout.flush()
                    i += 1
            print "\n"
            c += 1

    def make_all(self, branch):
        if len(sys.argv) == 1:
            self.download_code(branch)
        else:
            self.download_code(sys.argv[1])
        self.compile_docs()
        self.pack_latex()
        self.copy_docs()

doc = Documents()
if len(sys.argv) == 1:
    doc.make_all('master')
else:
    doc.make_all(sys.argv[1])
