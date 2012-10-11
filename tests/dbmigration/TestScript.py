# This script is the test script for db_comparison script 
# It makes 2 new web2py apps to compare
# Just run the test script to compare
# i.e python applications/eden/tests/dbmigration/TestScript.py

import os
import sys
import shutil
import subprocess

# Calculate Paths
own_path = os.path.realpath(__file__)
own_path = own_path.split(os.path.sep)
index_application = own_path.index("applications")
CURRENT_EDEN_APP  = own_path[index_application + 1]
WEB2PY_PATH = (os.path.sep).join(own_path[0:index_application])
NEW_APP = "TestDBMigrate_new"
OLD_APP = "TestDBMigrate_old"
NEW_PATH = "%s/applications/%s" % (WEB2PY_PATH, NEW_APP)
OLD_PATH = "%s/applications/%s" % (WEB2PY_PATH, OLD_APP)
OLD_TEST_PATH = "%s/applications/%s/tests/dbmigration/old_models" % (WEB2PY_PATH, CURRENT_EDEN_APP)
NEW_TEST_PATH = "%s/applications/%s/tests/dbmigration/new_models" % (WEB2PY_PATH, CURRENT_EDEN_APP)

if not "WEB2PY_PATH" in os.environ:
    os.environ["WEB2PY_PATH"] = WEB2PY_PATH

# Make 2 Apps for the Tests, and load their models from the files in the test
os.chdir("%s/applications" % (os.environ["WEB2PY_PATH"]))
sys.path.append("%s/applications" % (os.environ["WEB2PY_PATH"]))
os.mkdir(OLD_APP)
os.mkdir(NEW_APP)

# -----------------------------------------------------------------------------
def make_app(app_name, test_path_name):
    """
        Make the app with the appropriate model 
    """

    os.chdir("%s/applications/%s" % (os.environ["WEB2PY_PATH"], app_name))
    sys.path.append("%s/applications/%s" % (os.environ["WEB2PY_PATH"], app_name))
    os.mkdir("private")
    os.mkdir("databases")
    os.mkdir("models")
    os.mkdir("controllers")
    os.mkdir("cron")
    os.mkdir("languages")
    os.mkdir("cache")
    os.mkdir("modules")
    os.mkdir("static")
    os.mkdir("views")
    models_path = os.path.join(os.getcwd(), "models")
    src = os.listdir(test_path_name)
    for files in src:
        file_path = os.path.join(test_path_name, files)
        if (os.path.isfile(file_path)):
            shutil.copy(file_path, models_path)

make_app(OLD_APP, OLD_TEST_PATH)
make_app(NEW_APP, NEW_TEST_PATH)

# Run the comparison script
script = "python %s/applications/%s/static/scripts/Database_migration/apps_db_comparison.py %s %s %s" % \
    (WEB2PY_PATH, CURRENT_EDEN_APP, WEB2PY_PATH, OLD_APP, NEW_APP)
subprocess.call(script, shell=True)

# END =========================================================================
