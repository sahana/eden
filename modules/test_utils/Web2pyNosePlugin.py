
import nose
import re
from itertools import imap
import unittest

class Web2pyNosePlugin(nose.plugins.base.Plugin):
    # see: http://somethingaboutorange.com/mrl/projects/nose/0.11.1/plugins/writing.html
    
    """This plugin is designed to give the web2py environment to the tests.
    """
    score = 0
    # always enable as this plugin can only 
    # be selected by running this script
    enabled = True
    
    def __init__(
        self,
        application_name,
        environment,
        directory_pattern,
        test_folders
    ):
        super(Web2pyNosePlugin, self).__init__()
        self.application_name = application_name
        self.environment = environment
        self.directory_pattern = directory_pattern
        self.test_folders = test_folders
        
    def options(self, parser, env):
        """Register command line options"""
        pass
        
    def wantDirectory(self, dirname):
        return bool(re.search(self.directory_pattern, dirname))

    def wantFile(self, file_name):
        print file_name
        return file_name.endswith(".py") and any(
            imap(file_name.__contains__, self.test_folders)
        )

    def wantModule(self, module):
        return False

    def loadTestsFromName(self, file_name, discovered):
        """Sets up the unit-testing environment.
        
        This involves loading modules as if by web2py.
        Also we must have a test database.
        
        If testing controllers, tests need to set up the request themselves.
                
        """
        if file_name.endswith(".py"):
            
            # Is it possible that the module could load 
            # other code that is using the original db?
            
            test_globals = self.environment

            module_globals = dict(self.environment)
            # execfile is used because it doesn't create a module
            # or load the module from sys.modules if it exists.
            
            execfile(file_name, module_globals)
            
            import inspect
            # we have to return something, otherwise nose
            # will let others have a go, and they won't pass
            # in the web2py environment, so we'll get errors
            tests = []
    
            for name, thing in module_globals.iteritems():
                if (
                    # don't bother with globally imported things 
                    name not in test_globals \
                    # unless they have been overridden
                    or test_globals[name] is not thing
                ):
                    if (
                        isinstance(thing, type)
                        and issubclass(thing, unittest.TestCase)
                    ):
                        # look for test methods
                        for member_name in dir(thing):
                            if member_name.startswith("test"):
                                if callable(getattr(thing, member_name)):
                                    tests.append(thing(member_name))
                    elif (
                        name.startswith("test") 
                        or name.startswith("Test")
                    ):
                        if inspect.isfunction(thing):
                            function = thing
                            function_name = name
                            # things coming from execfile have no module
                            #print file_name, function_name, function.__module__
                            if function.__module__ in ("__main__", None):
                                tests.append(
                                    nose.case.FunctionTestCase(function)
                                )
            return tests
        else:
            return []
        
