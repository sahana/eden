# -*- coding: utf-8 -*-
#
# REST Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/s3/s3rest.py
#
import unittest
from gluon import *
from gluon.storage import Storage
from gluon.dal import Query
from s3.s3rest import S3Request

# =============================================================================
class URLBuilderTests(unittest.TestCase):

    def setUp(self):
        
        current.auth.override = True

        s3db = current.s3db
        ptable = s3db.pr_person
        ctable = s3db.pr_contact
        if not hasattr(self, "r"):
            record = current.db(ptable.pe_id == ctable.pe_id).select(
                                    ctable.id,
                                    ptable.id,
                                    limitby=(0, 1)).first()
            self.assertNotEqual(record, None)
            self.a = current.request.application
            self.p = str(record[ptable.id])
            self.c = str(record[ctable.id])
            self.r = S3Request(prefix="pr",
                               name="person",
                               c="pr",
                               f="person",
                               args=[self.p, "contact", self.c, "method"],
                               vars=Storage(format="xml", test="test"))

    def testURLConstruction(self):

        (a, p, c, r) = (self.a, self.p, self.c, self.r)
        self.assertEqual(r.url(),
                         "/%s/pr/person/%s/contact/%s/method.xml?test=test" % (a, p, c))

    def testURLMethodOverride(self):

        (a, p, c, r) = (self.a, self.p, self.c, self.r)

        # No change
        self.assertEqual(r.url(method=None),
                         "/%s/pr/person/%s/contact/%s/method.xml?test=test" % (a, p, c))

        # Set to None (resets target record ID)
        self.assertEqual(r.url(method=""),
                         "/%s/pr/person/%s/contact.xml?test=test" % (a, p))

        # Change method (retains target record ID)
        self.assertEqual(r.url(method="read"),
                         "/%s/pr/person/%s/contact/%s/read.xml?test=test" % (a, p, c))

        # Test without component
        r = S3Request(prefix="pr",
                      name="person",
                      c="pr",
                      f="person",
                      args=[self.p, "method"],
                      vars=Storage(format="xml", test="test"))

        # No change
        self.assertEqual(r.url(method=None),
                         "/%s/pr/person/%s/method.xml?test=test" % (a, p))

        # Set to None (resets target record ID and method)
        self.assertEqual(r.url(method=""),
                         "/%s/pr/person.xml?test=test" % a)

        # Change method (retains target record ID)
        self.assertEqual(r.url(method="read"),
                         "/%s/pr/person/%s/read.xml?test=test" % (a, p))

    def testURLRepresentationOverride(self):

        (a, p, c, r) = (self.a, self.p, self.c, self.r)

        # No change
        self.assertEqual(r.url(representation=None),
                         "/%s/pr/person/%s/contact/%s/method.xml?test=test" % (a, p, c))

        # Set to None (uses default)
        self.assertEqual(r.url(representation=""),
                         "/%s/pr/person/%s/contact/%s/method?test=test" % (a, p, c))

        # Change representation
        self.assertEqual(r.url(representation="pdf"),
                         "/%s/pr/person/%s/contact/%s/method.pdf?test=test" % (a, p, c))

    def testURLMasterIDOverride(self):

        (a, p, c, r) = (self.a, self.p, self.c, self.r)

        # No change
        self.assertEqual(r.url(id=None),
                         "/%s/pr/person/%s/contact/%s/method.xml?test=test" % (a, p, c))

        # Set to None (retains component ID and method)
        self.assertEqual(r.url(id=""),
                         "/%s/pr/person/contact/%s/method.xml?test=test" % (a, c))
        self.assertEqual(r.url(id=0),
                         "/%s/pr/person/contact/%s/method.xml?test=test" % (a, c))

        # Same ID (retains component ID and method)
        self.assertEqual(r.url(id=p),
                         "/%s/pr/person/%s/contact/%s/method.xml?test=test" % (a, p, c))
        # Change ID (resets component ID and method)
        self.assertEqual(r.url(id=5),
                         "/%s/pr/person/5/contact.xml?test=test" % a)

        # Set to wildcard (resets component ID and method)
        self.assertEqual(r.url(id="[id]"),
                         "/%s/pr/person/%%5Bid%%5D/contact.xml?test=test" % a)
        self.assertEqual(r.url(id="*"),
                         "/%s/pr/person/%%5Bid%%5D/contact.xml?test=test" % a)
        self.assertEqual(r.url(id=[]),
                         "/%s/pr/person/%%5Bid%%5D/contact.xml?test=test" % a)

    def testURLComponentOverride(self):

        (a, p, c, r) = (self.a, self.p, self.c, self.r)

        # No change
        self.assertEqual(r.url(component=None),
                         "/%s/pr/person/%s/contact/%s/method.xml?test=test" % (a, p, c))
        self.assertEqual(r.url(component="contact"),
                         "/%s/pr/person/%s/contact/%s/method.xml?test=test" % (a, p, c))

        # Set to None (resets component ID and method)
        self.assertEqual(r.url(component=""),
                         "/%s/pr/person/%s.xml?test=test" % (a, p))
                         
        # Change component (resets component ID and method)
        self.assertEqual(r.url(component="other"),
                         "/%s/pr/person/%s/other.xml?test=test" % (a, p))

    def testURLComponentIDOverride(self):

        (a, p, c, r) = (self.a, self.p, self.c, self.r)

        # No change
        self.assertEqual(r.url(component_id=None),
                         "/%s/pr/person/%s/contact/%s/method.xml?test=test" % (a, p, c))

        # Set to None (resets the method)
        self.assertEqual(r.url(component_id=0),
                         "/%s/pr/person/%s/contact.xml?test=test" % (a, p))

        # Change component ID (retains method)
        self.assertEqual(r.url(component_id=5),
                         "/%s/pr/person/%s/contact/5/method.xml?test=test" % (a, p))

    def testURLTargetOverrideMaster(self):
        
        (a, p, c, r) = (self.a, self.p, self.c, self.r)
        r = S3Request(prefix="pr",
                      name="person",
                      c="pr",
                      f="person",
                      args=[self.p, "method"],
                      vars=Storage(format="xml", test="test"))

        # No change
        self.assertEqual(r.url(target=None),
                         "/%s/pr/person/%s/method.xml?test=test" % (a, p))
        self.assertEqual(r.url(target=p),
                         "/%s/pr/person/%s/method.xml?test=test" % (a, p))

        # Set to None (resets method)
        self.assertEqual(r.url(target=0),
                         "/%s/pr/person.xml?test=test" % a)

        # Change target ID (retains method)
        self.assertEqual(r.url(target=5),
                         "/%s/pr/person/5/method.xml?test=test" % a)

    def testURLTargetOverrideComponent(self):

        (a, p, c, r) = (self.a, self.p, self.c, self.r)

        # No change
        self.assertEqual(r.url(target=None),
                         "/%s/pr/person/%s/contact/%s/method.xml?test=test" % (a, p, c))
        self.assertEqual(r.url(target=p),
                         "/%s/pr/person/%s/contact/%s/method.xml?test=test" % (a, p, c))

        # Set to None (resets method)
        self.assertEqual(r.url(target=0),
                         "/%s/pr/person/%s/contact.xml?test=test" % (a, p))

        # Change target ID (retains method)
        self.assertEqual(r.url(target=5),
                         "/%s/pr/person/%s/contact/5/method.xml?test=test" % (a, p))

    def testURLVarsOverride(self):

        (a, p, c, r) = (self.a, self.p, self.c, self.r)
        
        # No Change
        self.assertEqual(r.url(vars=None),
                         "/%s/pr/person/%s/contact/%s/method.xml?test=test" % (a, p, c))
                         
        # Set to None
        self.assertEqual(r.url(vars={}),
                         "/%s/pr/person/%s/contact/%s/method.xml" % (a, p, c))
        self.assertEqual(r.url(vars=""),
                         "/%s/pr/person/%s/contact/%s/method.xml" % (a, p, c))
                         
        # Change vars
        self.assertEqual(r.url(vars={"other":"test"}),
                         "/%s/pr/person/%s/contact/%s/method.xml?other=test" % (a, p, c))

    def testURLCombinations(self):

        (a, p, c, r) = (self.a, self.p, self.c, self.r)

        # Test request with component + component ID
        self.assertEqual(r.url(method="", id=5),
                         "/%s/pr/person/5/contact.xml?test=test" % a)
        self.assertEqual(r.url(method="", vars=None),
                         "/%s/pr/person/%s/contact.xml?test=test" % (a, p))
        self.assertEqual(r.url(id="[id]", method="review"),
                         "/%s/pr/person/%%5Bid%%5D/contact/review.xml?test=test" % a)
        self.assertEqual(r.url(method="deduplicate", target=0, vars={}),
                         "/%s/pr/person/%s/contact/deduplicate.xml" % (a, p))

        # Test request with component (without component ID)
        r = S3Request(prefix="pr",
                      name="person",
                      c="pr",
                      f="person",
                      args=[self.p, "contact", "method"],
                      vars=Storage(format="xml", test="test"))

        self.assertEqual(r.url(method="", id=5),
                         "/%s/pr/person/5/contact.xml?test=test" % a)
        self.assertEqual(r.url(method="", vars=None),
                         "/%s/pr/person/%s/contact.xml?test=test" % (a, p))
        self.assertEqual(r.url(id="[id]", method="review"),
                         "/%s/pr/person/%%5Bid%%5D/contact/review.xml?test=test" % a)
        self.assertEqual(r.url(method="deduplicate", target=0, vars={}),
                         "/%s/pr/person/%s/contact/deduplicate.xml" % (a, p))

        # Test request without component
        r = S3Request(prefix="pr",
                      name="person",
                      c="pr",
                      f="person",
                      args=[self.p, "method"],
                      vars=Storage(format="xml", test="test"))
        
        self.assertEqual(r.url(method="", id=5),
                         "/%s/pr/person/5.xml?test=test" % a)
        self.assertEqual(r.url(method="", vars=None),
                         "/%s/pr/person.xml?test=test" % a)
        self.assertEqual(r.url(id="[id]", method="review"),
                         "/%s/pr/person/%%5Bid%%5D/review.xml?test=test" % a)
        self.assertEqual(r.url(method="deduplicate", target=0, vars={}),
                         "/%s/pr/person/deduplicate.xml" % a)

    def tearDown(self):

        current.auth.override = False

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
        URLBuilderTests,
    )

# END ========================================================================
