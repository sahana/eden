# S3Search Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/s3/s3search.py

import unittest

from gluon import *
from s3.s3search import *

# =============================================================================
class TestS3SearchSimpleWidget(unittest.TestCase):
    """
        Test the S3SearchSimpleWidget to make sure it can create queries for
        real and virtual fields.
    """

    def setUp(self):
        # This is where I should create a resource and filters
        self.resource = current.s3db.resource("hrm_human_resource")
        self.widget = S3SearchSimpleWidget(field="person_id$first_name", _size=20)
        self.virtual_field_widget = S3SearchSimpleWidget(field="course")

    def test_query(self):
        # Test the query method.

        # Pass no value
        self.assertEqual(self.widget.query(self.resource, ""), None)

        # Pass a single value
        self.assertNotEqual(self.widget.query(self.resource, "1"), None)

        # Pass space-separated values
        self.assertNotEqual(self.widget.query(self.resource, "two values"), None)

        # Test against virtual field
        self.assertNotEqual(self.virtual_field_widget.query(self.resource, "value"), None)

    def test_widget(self):
        # Test the default HTML widget
        self.assertEqual(str(self.widget.widget(self.resource)),
                         str(INPUT(_id="human_resource_search_simple",
                                   _name="human_resource_search_simple",
                                   _size="20",
                                   _type="text")))

        # Test the widget with extra values
        self.assertEqual(str(self.widget.widget(self.resource,
                                                value="search string")),
                         str(INPUT(_id="human_resource_search_simple",
                                   _name="human_resource_search_simple",
                                   _size="20",
                                   _type="text",
                                   _value="search string")))

# =============================================================================
class TestS3SearchOptionsWidget(unittest.TestCase):
    """
        Test S3SearchOptionsWidget
    """

    def setUp(self):
        self.resource = current.s3db.resource("hrm_human_resource")

    def testQuery(self):
        # Test the query method
        pass

    def testWidget(self):
        T = current.T
        # Test the widget method

        # Test the widget method with a virtual field and no options
        widget = S3SearchOptionsWidget("virtual_field",
                                       options={})
        output = widget.widget(self.resource, {})
        self.assertEqual(str(output),
                         str(SPAN(T("No options available"),
                                  _class="no-options-available")))

        # Test widget with virtual field and one option.
        # Should return no-options message.
        # - no longer!
        #widget = S3SearchOptionsWidget("virtual_field",
        #                               options={1:"One"})
        #output = widget.widget(self.resource, {})
        #self.assertEqual(str(output),
        #                 str(SPAN(T("No options available"),
        #                          _class="no-options-available")))

        # Test widget with virtual field and multiple options.
        widget = S3SearchOptionsWidget("virtual_field",
                                       options={1:"One", 2:"Two"})
        output = widget.widget(self.resource, {})
        self.assertEqual(str(output),
                         str(TABLE(TR(TD(INPUT(_name="human_resource_search_select_virtual_field",
                                               _id="id-human_resource_search_select_virtual_field-0",
                                               _type="checkbox",
                                               _value="1"),
                                         LABEL("One",
                                               _for="id-human_resource_search_select_virtual_field-0"),
                                         ),
                                      ),
                                   TR(TD(INPUT(_name="human_resource_search_select_virtual_field",
                                               _id="id-human_resource_search_select_virtual_field-1",
                                               _type="checkbox",
                                               _value="2"),
                                         LABEL("Two",
                                               _for="id-human_resource_search_select_virtual_field-1")
                                         )
                                      ),
                                   _class="s3-checkboxes-widget",
                                   _name="human_resource_search_select_virtual_field_widget")))

# =============================================================================
class TestS3SearchMinMaxWidget(unittest.TestCase):
    """
        Test S3SearchOptionsWidget
    """

    def setUp(self):
        #self.resource = current.s3db.resource("inv_track_item")
        pass

    def testQuery(self):
        # Test the query method
        pass

    def testWidgetLabel(self):
        # Test the widget label method
        output = S3SearchMinMaxWidget.widget_label(dict(name="wname",
                                                        label="wlabel"))

        self.assertEqual(str(output),
                         str(LABEL("wlabel", _for="id-wname")))

    def testWidgetInput(self):
        # Test the widget label method
        output = S3SearchMinMaxWidget.widget_input(dict(name="wname",
                                                        label="wlabel",
                                                        requires="",
                                                        attributes=dict(_class="wclass")))

        self.assertEqual(str(output),
                         str(INPUT(_name="wname", _id="id-wname", _class="wclass")))


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
        self.assertEqual(i, "%s-%s-data" % (resource.alias, widget._class))

        v = attr["_value"]
        self.assertEqual(v, "~.name|~.organisation_id$name")
            
    def testSelector(self):
        """ Test construction of the URL query selector for a filter widget """

        fields = "name"
        s3db = current.s3db

        resource = s3db.resource("org_organisation")
        label, selector = S3FilterWidget._selector(resource, fields)
        self.assertEqual(selector, "~.name")

        fields = "nonexistent_component.name"

        resource = s3db.resource("org_organisation")
        label, selector = S3FilterWidget._selector(resource, fields)
        self.assertEqual(selector, None)

        fields = ["name", "organisation_id$name"]

        resource = s3db.resource("org_office")
        label, selector = S3FilterWidget._selector(resource, fields)
        self.assertEqual(selector, "~.name|~.organisation_id$name")

        fields = []

        resource = s3db.resource("org_organisation")
        label, selector = S3FilterWidget._selector(resource, fields)
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
        TestS3SearchSimpleWidget,
        TestS3SearchOptionsWidget,
        TestS3SearchMinMaxWidget,
        S3FilterWidgetTests,
    )

# END ========================================================================
