# -*- coding: utf-8 -*-
#
# REST Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3rest.py
#
import unittest
from gluon import *
from gluon.storage import Storage

from s3.s3rest import S3Request
from s3compat import StringIO

from unit_tests import run_suite

# =============================================================================
class POSTFilterTests(unittest.TestCase):
    """ Tests for POST filter queries """

    # -------------------------------------------------------------------------
    def setUp(self):

        request = current.request
        self.request_body = request._body
        self.content_type = request.env.content_type

    # -------------------------------------------------------------------------
    def tearDown(self):

        request = current.request
        request._body = self.request_body
        request.env.content_type = self.content_type

    # -------------------------------------------------------------------------
    def testPOSTFilter(self):
        """ Test POST filter interpretation with multipart request body """

        assertEqual = self.assertEqual
        assertNotIn = self.assertNotIn
        assertIn = self.assertIn

        request = current.request
        request.env.content_type = "multipart/form-data"

        # Test with valid filter expression JSON
        r = S3Request(prefix = "org",
                      name = "organisation",
                      http = "POST",
                      get_vars = {"$search": "form", "test": "retained"},
                      post_vars = {"~.name|~.comments__like": '''["first","second"]''',
                                   "~.other_field__lt": '''"1"''',
                                   "multi.nonstr__belongs": '''[1,2,3]''',
                                   "service_organisation.service_id__belongs": "1",
                                   "other": "testing",
                                   },
                      )

        # Method changed to GET:
        assertEqual(r.http, "GET")
        get_vars = r.get_vars
        post_vars = r.post_vars

        # $search removed from GET vars:
        assertNotIn("$search", get_vars)

        # Filter queries from POST vars JSON-decoded and added to GET vars:
        assertEqual(get_vars.get("~.name|~.comments__like"), ["first", "second"])
        assertEqual(get_vars.get("~.other_field__lt"), "1")

        # Edge-cases (non-str values) properly converted:
        assertEqual(get_vars.get("multi.nonstr__belongs"), ["1", "2", "3"])
        assertEqual(get_vars.get("service_organisation.service_id__belongs"), "1")

        # Filter queries removed from POST vars:
        assertNotIn("~.name|~.comments__like", post_vars)
        assertNotIn("~.other_field__lt", post_vars)
        assertNotIn("service_organisation.service_id__belongs", post_vars)

        # Non-queries retained in POST vars:
        assertIn("other", post_vars)

        # Must retain other GET vars:
        assertEqual(get_vars.get("test"), "retained")

        # Test without $search
        r = S3Request(prefix = "org",
                      name = "organisation",
                      http = "POST",
                      get_vars = {"test": "retained"},
                      post_vars = {"service_organisation.service_id__belongs": "1",
                                   "other": "testing",
                                   },
                      )

        # Method should still be POST:
        assertEqual(r.http, "POST")
        get_vars = r.get_vars
        post_vars = r.post_vars

        # $search never was in GET vars - confirm this to exclude test regression
        assertNotIn("$search", get_vars)

        # Filter queries from POST vars not added to GET vars:
        assertNotIn("service_organisation.service_id__belongs", get_vars)

        # Filter queries still in POST vars:
        assertIn("service_organisation.service_id__belongs", post_vars)

        # Must retain other GET vars:
        assertEqual(get_vars.get("test"), "retained")

    # -------------------------------------------------------------------------
    def testPOSTFilterAjax(self):
        """ Test POST filter interpretation with JSON request body """

        assertEqual = self.assertEqual
        assertNotIn = self.assertNotIn

        request = current.request

        # Test with valid filter expression JSON
        jsonstr = '''{"service_organisation.service_id__belongs":"1","~.example__lt":1,"~.other__like":[1,2],"~.name__like":"*Liquiçá*"}'''
        request._body = StringIO(jsonstr)
        r = S3Request(prefix = "org",
                      name = "organisation",
                      http = "POST",
                      get_vars = {"$search": "ajax", "test": "retained"},
                      )

        # Method changed to GET:
        assertEqual(r.http, "GET")
        get_vars = r.get_vars

        # $search removed from GET vars:
        assertNotIn("$search", get_vars)

        # Verify that parsed $filter vars can safely be re-encoded as GET URL
        try:
            r.url()
        except (UnicodeDecodeError, UnicodeEncodeError):
            self.fail("r.url raises Unicode exception with non-ASCII characters in $filter")

        # Filter queries from JSON body added to GET vars (always str, or list of str):
        assertEqual(get_vars.get("service_organisation.service_id__belongs"), "1")
        assertEqual(get_vars.get("~.example__lt"), "1")
        assertEqual(get_vars.get("~.other__like"), ["1", "2"])
        assertEqual(get_vars.get("~.name__like"), "*Liquiçá*")

        # Must retain other GET vars:
        assertEqual(get_vars.get("test"), "retained")

        # Test without $search
        request._body = StringIO('{"service_organisation.service_id__belongs":"1"}')
        r = S3Request(prefix = "org",
                      name = "organisation",
                      http = "POST",
                      get_vars = {"test": "retained"},
                      )

        # Method should still be POST:
        assertEqual(r.http, "POST")
        get_vars = r.get_vars

        # $search never was in GET vars - confirm this to exclude test regression
        assertNotIn("$search", get_vars)

        # Filter queries from JSON body not added to GET vars:
        assertNotIn("service_organisation.service_id__belongs", get_vars)

        # Must retain other GET vars:
        assertEqual(get_vars.get("test"), "retained")

        # Test with valid JSON but invalid filter expression
        request._body = StringIO('[1,2,3]')
        r = S3Request(prefix = "org",
                      name = "organisation",
                      http = "POST",
                      get_vars = {"$search": "ajax", "test": "retained"},
                      )

        # Method changed to GET:
        assertEqual(r.http, "GET")
        get_vars = r.get_vars

        # $search removed from GET vars:
        assertNotIn("$search", get_vars)

        # Filter queries from JSON body not added to GET vars:
        assertNotIn("service_organisation.service_id__belongs", get_vars)

        # Must retain other GET vars:
        assertEqual(get_vars.get("test"), "retained")

        # Test with empty body
        request._body = StringIO('')
        r = S3Request(prefix = "org",
                      name = "organisation",
                      http = "POST",
                      get_vars = {"$search": "ajax", "test": "retained"},
                      )

        # Method changed to GET:
        assertEqual(r.http, "GET")
        get_vars = r.get_vars

        # $search removed from GET vars:
        assertNotIn("$search", get_vars)

        # Filter queries from JSON body not added to GET vars:
        assertNotIn("service_organisation.service_id__belongs", get_vars)

        # Must retain other GET vars:
        assertEqual(get_vars.get("test"), "retained")

# =============================================================================
class URLBuilderTests(unittest.TestCase):

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.auth.override = False

    # -------------------------------------------------------------------------
    def testURLConstruction(self):

        (a, p, c, r) = (self.a, self.p, self.c, self.r)
        self.assertEqual(r.url(),
                         "/%s/pr/person/%s/contact/%s/method.xml?test=test" % (a, p, c))

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    def testURLTargetOverrideComponent(self):

        (a, p, c, r) = (self.a, self.p, self.c, self.r)

        # No change
        self.assertEqual(r.url(target=None),
                         "/%s/pr/person/%s/contact/%s/method.xml?test=test" % (a, p, c))
        self.assertEqual(r.url(target=c),
                         "/%s/pr/person/%s/contact/%s/method.xml?test=test" % (a, p, c))

        # Set to None (resets method)
        self.assertEqual(r.url(target=0),
                         "/%s/pr/person/%s/contact.xml?test=test" % (a, p))

        # Change target ID (retains method)
        self.assertEqual(r.url(target=5),
                         "/%s/pr/person/%s/contact/5/method.xml?test=test" % (a, p))

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
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

# =============================================================================
if __name__ == "__main__":

    run_suite(
        POSTFilterTests,
        URLBuilderTests,
    )

# END ========================================================================
