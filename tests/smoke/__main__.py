
"""
    'Smoke test' script
    
    - traverse .py files in the controllers folder
    - find all functions without arguments defined within those modules
    - execute them with a 'fresh'ish empty request
    - report any problems
"""

import os
import inspect
import glob
import traceback
import gluon

# @ToDo: use os.walk in order to recurse into folders
passes = 0
fails = 0
module_fails = []
application_name = request.application

controller_folder_path = "applications/%s/controllers/*.py" % application_name
for module_path in glob.glob(controller_folder_path):
    print
    print module_path
    test_globals = globals()
    module_globals = dict(test_globals)
    controller_name = module_path[module_path.rindex("/")+1:-3]
    request.controller = controller_name
    if controller_name not in deployment_settings.modules:
        deployment_settings.modules[controller_name] = Storage()
    try:
        execfile(module_path, module_globals)
    except BaseException, exception:
        print "MODULE FAIL:", module_path, exception
        traceback.print_exc()
        module_fails.append(controller_name)
    else:
        for name, thing in module_globals.iteritems():
            if (
                # don't bother with globally imported things 
                name not in test_globals \
                # unless they have been overridden
                or test_globals[name] is not thing
            ):
                if inspect.isfunction(thing):
                    function = thing
                    function_name = name
                    # things coming from execfile have no module
                    if function.__module__ is None:
                        # controllers should have no arguments
                        if len(inspect.getargspec(function).args) == 0:
                            try:
                                # create request
                                # TODO: avoid reusing request by either:
                                # inserting new request into function's globals
                                # or reloading the module for each function  
                                request.function = function_name
                                request.vars = Storage()
                                request.args = Storage()
                                env = request.env
                                env['path_info'] = '/%s/%s/%s' % (
                                    application_name,
                                    controller_name,
                                    function_name
                                )
                                env['get_vars'] = Storage()
                                env['post_vars'] = Storage()
                                function()
                            except (gluon.http.HTTP), http_exception:
                                # these are considered normal
                                print " PASS: %s/%s" % (
                                    controller_name,
                                    function_name
                                    )
                                passes += 1
                            except BaseException, exception:
                                print
                                print " FAIL: %s/%s" % (
                                    controller_name,
                                    function_name
                                )
                                traceback.print_exc()
                                fails += 1
                            else:
                                print " PASS: %s/%s" % (
                                    controller_name,
                                    function_name
                                )
                                passes += 1

print passes, "passes"
print fails, "fails"
print passes+fails, "total"
print "Module fails:", ", ".join(module_fails)
