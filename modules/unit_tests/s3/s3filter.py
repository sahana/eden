# S3Filter Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3filter.py

import unittest

from gluon import *
from s3.s3filter import *

# =============================================================================
class S3FilterWidgetTests(unittest.TestCase):
    """ Tests for S3FilterWidget base class helper methods """

    def testInit(self):
        """ Test filter widget constructor """

        widget = S3FilterWidget(["name", "organisation_id$name"],
                                option="test option",
                                _class="test-class")

        self.assertTrue("option" in widget.opts)
        self.assertTrue(len(widget.opts), 1)
        self.assertTrue(widget.opts["option"] == "test option")

        self.assertTrue("_class" in widget.attr)
        self.assertTrue(len(widget.attr), 1)
        self.assertTrue(widget.attr["_class"] == "test-class")

    def testRender(self):
        """ Test rendering of the hidden data element """

        widget = S3FilterWidget(["name", "organisation_id$name"])

        # Override widget renderer
        widget.widget = lambda resource, values: ""

        resource = current.s3db.resource("org_office")

        output = widget(resource, get_vars={})
        self.assertTrue(isinstance(output[0], INPUT))

        # Check attributes of the hidden data element
        attr = output[0].attributes

        t = attr["_type"]
        self.assertEqual(t, "hidden")

        c = attr["_class"]
        # Generic class
        self.assertTrue("filter-widget-data" in c)
        # Widget-type-specific class
        self.assertTrue("%s-data" % widget._class in c)

        i = attr["_id"]
        self.assertEqual(i, "%s-org_office_name-org_organisation_name-%s-data" %
                        (resource.alias, widget._class))

        v = attr["_value"]
        self.assertEqual(v, "~.name|~.organisation_id$name")

    def testSelector(self):
        """ Test construction of the URL query selector for a filter widget """

        fields = "name"
        s3db = current.s3db

        widget = S3FilterWidget()

        resource = s3db.resource("org_organisation")
        label, selector = widget._selector(resource, fields)
        self.assertEqual(selector, "~.name")

        widget.alias = "organisation"
        label, selector = widget._selector(resource, fields)
        self.assertEqual(selector, "organisation.name")
        widget.alias = None

        fields = "nonexistent_component.name"

        resource = s3db.resource("org_organisation")
        label, selector = widget._selector(resource, fields)
        self.assertEqual(selector, None)

        fields = ["name", "organisation_id$name"]

        resource = s3db.resource("org_office")
        label, selector = widget._selector(resource, fields)
        self.assertEqual(selector, "~.name|~.organisation_id$name")

        fields = []

        resource = s3db.resource("org_organisation")
        label, selector = widget._selector(resource, fields)
        self.assertEqual(selector, None)

    def testVariable(self):
        """ Test construction of the URL variable for filter widgets """

        variable = S3FilterWidget._variable("organisation.name", "like")
        self.assertEqual(variable, "organisation.name__like")

        variable = S3FilterWidget._variable("organisation.name", None)
        self.assertEqual(variable, "organisation.name")

        variable = S3FilterWidget._variable("organisation.name", "")
        self.assertEqual(variable, "organisation.name")

        variable = S3FilterWidget._variable("organisation.name", ("ge", "le"))
        self.assertEqual(variable, ["organisation.name__ge",
                                    "organisation.name__le"])

    def testValues(self):
        """ Test extraction of filter widget values from GET vars """

        get_vars = {"test_1": "1",
                    "test_2": ["1,2", "3"]}

        values = S3FilterWidget._values(get_vars, "test_1")
        self.assertEqual(len(values), 1)
        self.assertTrue("1" in values)

        values = S3FilterWidget._values(get_vars, "test_2")
        self.assertEqual(len(values), 3)
        self.assertTrue("1" in values)
        self.assertTrue("2" in values)
        self.assertTrue("3" in values)

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
        S3FilterWidgetTests,
    )

# END ========================================================================
