"""
    Installation script for EdenTest
"""
from sys import exit
from importlib import import_module
from sys import exc_info, path
import os

def module_exists(module):
    """
        Check to see if a module is installed or not
    """
    try:
        import_module(module)
    except ImportError:
        return False
    else:
        return True

def easy_install(package):
   """
        Install the package using easy_install
   """
   try:
        easy.main(["-U", package])
        return True

   except:
        print "Unable to install %s using easy_install. Please read the instructions for \
        manual installation.. Exiting" % package
        print "Error: %s: %s" % (exc_info()[0] ,exc_info()[1])
        return False

def pip_install(package):
    """
        Install the package using pip
    """
    try:
        pip.main(["install", "--upgrade", package])
        return True

    except:
        print "Unable to install %s using pip. Please read the instructions for \
        manual installation.. Exiting" % package
        print "Error: %s: %s" % (exc_info()[0] ,exc_info()[1])
        return False

if __name__ == "__main__":

    if module_exists("pip"):
        import pip
        print "Installing packages with pip ..."

        if not pip_install("robotframework"):
            print "Could not install Robot Framework. Exiting..."
            exit(1)

        if not pip_install("robotframework-selenium2library"):
            print "Could not install Selenium2Library. Exiting..."
            exit(1)

        if not pip_install("robotframework-databaselibrary"):
            print "Could not install DatabaseLibrary. Exiting..."
            exit(1)

        print "Installation successful"
        exit(0)

    elif module_exists("setuptools.command.easy_install"):
        import setuptools.command.easy_install as easy
        print "Installing packages with easy_install ..."

        if not easy_install("robotframework"):
            print "Could not install Robot Framework. Exiting..."
            exit(1)

        if not easy_install("robotframework-databaselibrary"):
            print "Could not install DatabaseLibrary. Exiting..."
            exit(1)

        # installing the dependencies of Selenium2Library
        easy_install("selenium")
        easy_install("decorator")
        easy_install("docutils")
        if not easy_install("robotframework-selenium2library"):
            print "Could not install Selenium2Library. Exiting..."
            exit(1)

        print "Installation successful"
        exit(0)
