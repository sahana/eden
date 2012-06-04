# S3Search Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/s3/s3search.py

import unittest

from gluon import current
from s3.s3search import S3SearchSimpleWidget, S3SearchOptionsWidget

# =============================================================================
class TestS3SearchSimpleWidget(unittest.TestCase):
    """
        Test the S3SearchSimpleWidget to make sure it can create queries for
        real and virtual fields.
    """

    def setUp(self):
        # This is where I should create a resource and filters
        self.resource = current.manager.define_resource("hrm", "human_resource")
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
                         '<input name="human_resource_search_simple" size="20" type="text" />')

        # Test the widget with extra values
        self.assertEqual(str(self.widget.widget(self.resource, value="search string")),
                         '<input name="human_resource_search_simple" size="20" type="text" value="search string" />')

# =============================================================================
class TestS3SearchOptionsWidget(unittest.TestCase):
    """
        Test S3SearchOptionsWidget
    """

    def setUp(self):
        self.resource = current.manager.define_resource("hrm", "human_resource")

    def testQuery(self):
        # Test the query method
        pass

    def testWidget(self):
        # Test the widget method

        # Test the widget method with a virtual field and custom options
        widget = S3SearchOptionsWidget("virtual_field",
                                       options={})
        output = widget.widget(self.resource, {})
        self.assertEqual(str(output),
                         str(SPAN(T("No options available"),
                                  _class="no-options-available")))

        # Test the widget method with a virtual field and custom options
        widget = S3SearchOptionsWidget("virtual_field",
                                       options={1:"One"})
        output = widget.widget(self.resource, {})
        self.assertEqual(str(output),
                         str(TABLE(TR(TD(LABEL(INPUT(_name="human_resource_search_select_virtual_field",
                                                     _type="checkbox",
                                                     _value="1"),
                                               "One"))),
                                   _class="generic-widget",
                                   _id="None_human_resource_search_select_virtual_field",
                                   _name="human_resource_search_select_virtual_field")))



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
    )

# END ========================================================================
