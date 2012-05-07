# -*- coding: utf-8 -*-
#
# Project Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/eden/project.py
#
import unittest
import copy

from gluon import current
from gluon.globals import Request
from eden.project import *

import copy
# Create a test database that's laid out just like the "real" database
test_db = DAL('sqlite://testing.sqlite')  # Name and location of the test DB file
for tablename in db.tables:  # Copy tables!
    table_copy = [copy.copy(f) for f in db[tablename]]
    test_db.define_table(tablename, *table_copy)

db = test_db  # Rename the test database so that functions will use it instead of the real database
#execfile("applications/eden/controllers/project.py", globals())

current.db = db
s3db.load_all_models()

db(db.org_organisation.id>0).delete()
db(db.project_project.id>0).delete()
db(db.project_organisation.id>0).delete()
db.commit()

# =============================================================================
class ProjectOrganisationTests(unittest.TestCase):
    """ Project Tests """

    def setUp(self):
        #request = Request()  # Use a clean Request object
        db.project_project.insert(name="Test Project")
        db.org_organisation.insert(name="Test Organisation")
        db.commit()

    def test_project_organisation_ondelete(self):
        # Set variables for the test function
        #request.post_vars["game_id"] = 1
        #request.post_vars["username"] = "spiffytech"

        S3ProjectDRRModel.project_organisation_ondelete()
        db.commit()
        self.assertEquals(0, len(resp["games"]))

    # def testHomepageFunction(self):

    #     # Test existing module
    #     hp = homepage("pr")
    #     self.assertTrue(hp is not None)

    #     # Test non-existent (deactivated) module
    #     hp = homepage("nonexistent")
    #     self.assertTrue(hp is not None)
    #     self.assertFalse(hp.check_active())
    #     rendered_hp = hp.xml()
    #     self.assertEqual(rendered_hp, "")

    # def testAddResourceLink(self):

    #     comment = S3AddResourceLink(c="pr", f="person")

    #     # If the module is active, the comment should always be active
    #     self.assertEqual(comment.check_active(),
    #                      deployment_settings.has_module("pr"))
    #     self.assertEqual(comment.method, "create")

    #     # Label should fall back to CRUD string
    #     crud_string = s3base.S3CRUD.crud_string("pr_person", "label_create_button")
    #     self.assertEqual(comment.label, crud_string)

    #     if "dvi" in deployment_settings.modules:
    #         comment = S3AddResourceLink(c="dvi", f="body")
    #         # Deactivate module
    #         dvi = deployment_settings.modules["dvi"]
    #         del deployment_settings.modules["dvi"]
    #         # Comment should auto-deactivate
    #         self.assertFalse(comment.check_active())
    #         # Restore module
    #         deployment_settings.modules["dvi"] = dvi
    #         # Comment should auto-reactivate
    #         self.assertTrue(comment.check_active())

    #     self.assertFalse(comment.check_permission())
    #     self.assertEqual(comment.xml(), "")
    #     auth.s3_impersonate(1)
    #     self.assertTrue(comment.check_permission())
    #     output = comment.xml()
    #     self.assertTrue(type(output) is str)
    #     self.assertNotEqual(output, "")

# =============================================================================
def run_suite(*test_classes):
    """ Run the test suite """

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    if suite is not None:
        unittest.TextTestRunner().run(suite)
    return

if __name__ == "__main__":

    run_suite(
        ProjectOrganisationTests,
    )

# END ========================================================================
