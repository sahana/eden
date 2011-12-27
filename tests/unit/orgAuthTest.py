"""
    run as -
    $ python web2py.py -S vita -M -R applications/vita/tests/unit/orgAuthTest.py
"""

import sys
import glob
import unittest
from gluon.globals import Request

# Pre-requisites & settings
# -----------------------------------------------------------------------------
APP_NAME=request.application
sys.path.append("applications/" + APP_NAME + "/tests/unit")
import helpers

auth = db.auth
manager = db.manager
helpers.USE_TEST_DB = True
db = helpers.get_db(DAL, db, clean=True)

if helpers.USE_TEST_DB:
    # run models over test db for zzz_1st_roles, etc
    model_files = glob.glob('applications/'+APP_NAME+'/models/*.py')
    for model_file in model_files:
        execfile(model_file, globals())


# Unit Tests
# -----------------------------------------------------------------------------
class OrgAuthTests(unittest.TestCase):
    def setUp(self):
        #self.test_org_id = db.org_organisation.insert(
                                #name="OrgAuthTest Org 1",
                                #acronym="OATO1")
        pass

    #def test_create_record_roles(self):
        #auth.org.create_record_roles("org_organisation",
                                     #self.test_org_id)

        #scope = (auth.org.scope.ORG, auth.org.scope.BOTH)
        #rsttable = auth.org.table_role_set_template
        #rstable = auth.org.table_role_set

        #query = (rsttable.scope.belongs(scope))
        #role_set_templates_set = set([x.name for x in db(query).select()])

        #query = (rstable.organisation_id == self.test_org_id)
        #org_role_set_names = [x.name.split("_")[-1] for x in db(query).select()]
        #org_role_set_names_set = set(org_role_set_names)

        ## there should be only N roles for org if there are N in template scope
        #self.assertEqual(len(org_role_set_names), len(role_set_templates_set))

        ## the roles created should only be ones from the template scope
        ## neither any less, nor any extra
        #self.assertEqual(org_role_set_names_set, role_set_templates_set)

suite = unittest.TestSuite()
for test_case in (
    helpers.DBReplicationTest,
    OrgAuthTests,
    ):
    suite.addTest(unittest.makeSuite(test_case))

unittest.TextTestRunner(verbosity=2).run(suite)