# -*- coding: utf-8 -*-
#
# S3CRUD Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/s3/s3crud.py
#
import unittest
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

# =============================================================================
class S3CRUDValidateTests(unittest.TestCase):
    """ Test S3CRUD "validate" method """

    def setUp(self):

        manager = current.manager

        # Create a fake request
        self.resource = manager.define_resource("org", "organisation")
        self.request = Storage(prefix="org",
                               name="organisation",
                               resource=self.resource,
                               table=self.resource.table,
                               tablename=self.resource.tablename,
                               method="validate",
                               get_vars=Storage(),
                               representation="json",
                               http="GET")

    def testValidateMainTable(self):

        request = self.request
        crud = self.resource.crud

        jsonstr = """{"name":"TestOrganisation", "acronym":"TO"}"""
        request.body = StringIO(jsonstr)

        output = crud.validate(request)

        self.assertTrue(isinstance(output, basestring))
        from gluon.contrib import simplejson as json
        data = json.loads(output)
        self.assertTrue(isinstance(data, dict))
        self.assertEqual(len(data), 2)
        self.assertTrue("name" in data)
        name = data["name"]
        self.assertTrue(isinstance(name, dict))
        self.assertTrue("value" in name)
        self.assertTrue("text" in name)
        self.assertTrue(isinstance(name["text"], basestring))
        self.assertFalse("_error" in name)

        acronym = data["acronym"]
        self.assertTrue(isinstance(acronym, dict))
        self.assertTrue("value" in acronym)
        self.assertTrue("text" in acronym)
        self.assertTrue(isinstance(acronym["text"], basestring))
        self.assertFalse("_error" in acronym)

    def testValidateMainTableError(self):

        request = self.request
        crud = self.resource.crud

        jsonstr = """{"name":"", "acronym":"TO"}"""
        request.body = StringIO(jsonstr)

        output = crud.validate(request)

        self.assertTrue(isinstance(output, basestring))
        from gluon.contrib import simplejson as json
        data = json.loads(output)
        self.assertTrue(isinstance(data, dict))
        self.assertEqual(len(data), 2)
        self.assertTrue("name" in data)
        name = data["name"]
        self.assertTrue(isinstance(name, dict))
        self.assertTrue("value" in name)
        self.assertFalse("text" in name)
        self.assertTrue("_error" in name)

        acronym = data["acronym"]
        self.assertTrue(isinstance(acronym, dict))
        self.assertTrue("value" in acronym)
        self.assertTrue("text" in acronym)
        self.assertTrue(isinstance(acronym["text"], basestring))
        self.assertFalse("_error" in acronym)

    def testValidateComponentTable(self):

        request = self.request
        crud = self.resource.crud

        jsonstr = """{"name":"TestOffice"}"""
        request.body = StringIO(jsonstr)
        request.get_vars["component"] = "office"

        output = crud.validate(request)

        self.assertTrue(isinstance(output, basestring))
        from gluon.contrib import simplejson as json
        data = json.loads(output)
        self.assertTrue(isinstance(data, dict))
        self.assertEqual(len(data), 1)
        self.assertTrue("name" in data)
        name = data["name"]
        self.assertTrue(isinstance(name, dict))
        self.assertTrue("value" in name)
        self.assertTrue("text" in name)
        self.assertTrue(isinstance(name["text"], basestring))
        self.assertFalse("_error" in name)

    def testValidateComponentTableFailure(self):

        request = self.request
        crud = self.resource.crud

        jsonstr = """{"name":"", "acronym":"test"}"""
        request.body = StringIO(jsonstr)
        request.get_vars["component"] = "office"

        output = crud.validate(request)

        self.assertTrue(isinstance(output, basestring))
        from gluon.contrib import simplejson as json
        data = json.loads(output)
        self.assertTrue(isinstance(data, dict))
        self.assertEqual(len(data), 2)
        self.assertTrue("name" in data)
        name = data["name"]
        self.assertTrue(isinstance(name, dict))
        self.assertTrue("value" in name)
        self.assertFalse("text" in name)
        self.assertTrue("_error" in name)

        self.assertTrue("acronym" in data)
        acronym = data["acronym"]
        self.assertTrue(isinstance(acronym, dict))
        self.assertTrue("value" in acronym)
        self.assertFalse("text" in acronym)
        self.assertTrue("_error" in acronym)

    def tearDown(self):
        pass

# =============================================================================
def run_suite(*test_classes):
    """ Run the test suite """

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    if suite is not None:
        unittest.TextTestRunner(verbosity=2).run(suite)
    return

if __name__ == "__main__":

    run_suite(
        S3CRUDValidateTests,
    )

# END ========================================================================
