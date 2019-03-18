"""
    Installation script for EdenTest
"""
import os

from importlib import import_module
from sys import exc_info, exit, path, stderr

def info(string):
    stderr.write("%s\n" % string)

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
        info("Unable to install %s using easy_install." % package)
        info("Please read the instructions for manual installation.")
        info("Error: %s: %s" % (exc_info()[0] ,exc_info()[1]))
        return False

def pip_install(package):
    """
        Install the package using pip
    """
    try:
        if hasattr(pip, 'main'):
            pip.main(['install', "--upgrade", package])
        else:
            from pip._internal import main as pip_main
            pip_main(['install', "--upgrade", package])
        return True
    except:
        info("Unable to install %s using pip." % package)
        info("Please read the instructions for manual installation.")
        info("Error: %s: %s" % (exc_info()[0] ,exc_info()[1]))
        return False

if __name__ == "__main__":

    if module_exists("pip"):
        import pip
        info("Installing packages with pip ...")

        if not pip_install("robotframework"):
            info("Could not install Robot Framework.")
            exit(1)

        if not pip_install("robotframework-seleniumlibrary"):
            info("Could not install SeleniumLibrary.")
            exit(1)

        if not pip_install("requests"):
            info("Could not install Requests.")
            exit(1)

        if not pip_install("robotframework-databaselibrary"):
            info("Could not install DatabaseLibrary.")
            exit(1)

        info("Installation successful")
        exit(0)

    elif module_exists("setuptools.command.easy_install"):
        import setuptools.command.easy_install as easy
        info("Installing packages with easy_install ...")

        if not easy_install("robotframework"):
            info("Could not install Robot Framework.")
            exit(1)

        if not easy_install("robotframework-databaselibrary"):
            info("Could not install DatabaseLibrary.")
            exit(1)

        if not easy_install("requests"):
            info("Could not install Requests.")
            exit(1)

        # installing the dependencies of Selenium2Library
        easy_install("selenium")
        easy_install("decorator")
        easy_install("docutils")
        if not easy_install("robotframework-seleniumlibrary"):
            info("Could not install SeleniumLibrary.")
            exit(1)

        info("Installation successful")
        exit(0)
