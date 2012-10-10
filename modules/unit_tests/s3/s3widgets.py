# S3Search Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/s3/s3widgets.py

import unittest

from gluon import *
from gluon.storage import Storage
from s3.s3widgets import S3OptionsMatrixWidget, s3_checkboxes_widget, s3_grouped_checkboxes_widget
from gluon.contrib.simplejson.ordered_dict import OrderedDict

# =============================================================================
class TestS3OptionsMatrixWidget(unittest.TestCase):
    """
        Test the S3SearchSimpleWidget to make sure it can create queries for
        real and virtual fields.
    """

    def setUp(self):
        self.field = Storage(name='roles')

        self.rows = (
            ("Staff", "1", "2", "3", "4", "5"),
            ("Volunteers", "6", "7", "8", "9", "10"),
            ("Members", "11", "12", "13", "14", "15"),
            ("Warehouse", "16", "17", "18", "19", "20"),
            ("Assets", "21", "22", "23", "24", "25"),
            ("Projects", "26", "27", "28", "29", "30"),
            ("Assessments", "31", "32", "33", "34", "35"),
            ("Incidents", "36", "37", "38", "39", "40"),
        )

        self.columns = ("", "None", "Reader", "Data Entry", "Editor", "Super Editor")

        self.value = ("3", "24", "29", "39", "40")

        self.widget = S3OptionsMatrixWidget(self.rows, self.columns)

    def test_widget(self):
        # Test with just the required parameters
        expected_result = TABLE(THEAD(TR(TH("", _scope="col"),
                                         TH("None", _scope="col"),
                                         TH("Reader", _scope="col"),
                                         TH("Data Entry", _scope="col"),
                                         TH("Editor", _scope="col"),
                                         TH("Super Editor", _scope="col"),
                                )),
                                TBODY(TR(TH("Staff", _scope="row"),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="1"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="2"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="3"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="4"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="5"
                                                  ))
                                         ),
                                      TR(TH("Volunteers", _scope="row"),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="6"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="7"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="8"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="9"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="10"
                                                  ))
                                         ),
                                      TR(TH("Members", _scope="row"),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="11"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="12"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="13"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="14"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="15"
                                                  ))
                                         ),
                                      TR(TH("Warehouse", _scope="row"),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="16"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="17"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="18"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="19"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="20"
                                                  ))
                                         ),
                                      TR(TH("Assets", _scope="row"),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="21"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="22"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="23"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="24"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="25"
                                                  ))
                                         ),
                                      TR(TH("Projects", _scope="row"),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="26"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="27"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="28"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="29"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="30"
                                                  ))
                                         ),
                                      TR(TH("Assessments", _scope="row"),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="31"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="32"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="33"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="34"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="35"
                                                  ))
                                         ),
                                      TR(TH("Incidents", _scope="row"),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="36"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="37"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="38"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="39"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="40"
                                                  ))
                                         ),
                                    )
                                 )
        self.failUnlessEqual(str(self.widget(self.field, [])), str(expected_result))

    def test_values(self):
        # Test the widget with values
        expected_result = TABLE(THEAD(TR(TH("", _scope="col"),
                                         TH("None", _scope="col"),
                                         TH("Reader", _scope="col"),
                                         TH("Data Entry", _scope="col"),
                                         TH("Editor", _scope="col"),
                                         TH("Super Editor", _scope="col"),
                                )),
                                TBODY(TR(TH("Staff", _scope="row"),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="1"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="2"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="3",
                                                  value=True
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="4"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="5"
                                                  ))
                                         ),
                                      TR(TH("Volunteers", _scope="row"),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="6"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="7"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="8"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="9"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="10"
                                                  ))
                                         ),
                                      TR(TH("Members", _scope="row"),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="11"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="12"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="13"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="14"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="15"
                                                  ))
                                         ),
                                      TR(TH("Warehouse", _scope="row"),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="16"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="17"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="18"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="19"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="20"
                                                  ))
                                         ),
                                      TR(TH("Assets", _scope="row"),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="21"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="22"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="23"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="24",
                                                  value=True
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="25"
                                                  ))
                                         ),
                                      TR(TH("Projects", _scope="row"),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="26"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="27"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="28"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="29",
                                                  value=True
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="30"
                                                  ))
                                         ),
                                      TR(TH("Assessments", _scope="row"),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="31"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="32"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="33"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="34"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="35"
                                                  ))
                                         ),
                                      TR(TH("Incidents", _scope="row"),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="36"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="37"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="38"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="39",
                                                  value=True
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _name="roles",
                                                  _value="40",
                                                  value=True
                                                  ))
                                         ),
                                    )
                                 )
        self.assertEqual(str(self.widget(self.field, self.value)),
                         str(expected_result))


# =============================================================================
class TestS3CheckboxesWidget(unittest.TestCase):
    """
        Test s3_checkboxes_widget
    """

    def setUp(self):
        pass

    def testWidget(self):
        # Test the widget method
        field = Storage(name="f",
                        type="list:reference t_able",
                        requires=IS_IN_SET({1:"One", 2:"Two"},
                                           multiple=True))

        widget = s3_checkboxes_widget(field,
                                      [])
        self.assertEqual(str(widget),
                         str(TABLE(TR(TD(INPUT(_id="id-f-0",
                                               _name="f",
                                               _type="checkbox",
                                               _value="1"),
                                         LABEL("One",
                                               _for="id-f-0"))),
                                   TR(TD(INPUT(_id="id-f-1",
                                               _name="f",
                                               _type="checkbox",
                                               _value="2"),
                                         LABEL("Two",
                                               _for="id-f-1"))),
                                   _class="s3-checkboxes-widget",
                                   _name="f_widget")))

        widget = s3_checkboxes_widget(field,
                                      [1,])
        self.assertEqual(str(widget),
                         str(TABLE(TR(TD(INPUT(_id="id-f-0",
                                               _name="f",
                                               _type="checkbox",
                                               _value="1",
                                               value=True),
                                         LABEL("One",
                                               _for="id-f-0"))),
                                   TR(TD(INPUT(_id="id-f-1",
                                               _name="f",
                                               _type="checkbox",
                                               _value="2"),
                                         LABEL("Two",
                                               _for="id-f-1"))),
                                   _class="s3-checkboxes-widget",
                                   _name="f_widget")))

        widget = s3_checkboxes_widget(field,
                                      [1,],
                                      cols=2,
                                      start_at_id=5,
                                      _class="myclass")
        self.assertEqual(str(widget),
                         str(TABLE(TR(TD(INPUT(_id="id-f-5",
                                               _name="f",
                                               _type="checkbox",
                                               _value="1",
                                               value=True),
                                         LABEL("One",
                                               _for="id-f-5")),
                                      TD(INPUT(_id="id-f-6",
                                               _name="f",
                                               _type="checkbox",
                                               _value="2"),
                                         LABEL("Two",
                                               _for="id-f-6"))),
                                   _class="myclass",
                                   _name="f_widget")))


# =============================================================================
class TestS3GroupedCheckboxesWidget(unittest.TestCase):
    """
        Test s3_checkboxes_widget
    """

    def setUp(self):
        pass

    def testWidget(self):
        # Test the widget method
        field = Storage(name="f",
                        type="list:reference t_able",
                        requires=IS_IN_SET({1:"One", 2:"Two"},
                                           multiple=True))

        # default options
        widget = s3_grouped_checkboxes_widget(field, [])
        self.assertEqual(str(widget),
                         str(s3_checkboxes_widget(field, [])))

        # small group size
        widget = s3_grouped_checkboxes_widget(field,
                                              [],
                                              size=1)

        f1 = Storage(name="f",
                        type="list:reference t_able",
                        requires=IS_IN_SET({1:"One"},
                                           multiple=True))
        f2 = Storage(name="f",
                        type="list:reference t_able",
                        requires=IS_IN_SET({2:"Two"},
                                           multiple=True))
        self.assertEqual(str(widget),
                         str(TAG[""](DIV(DIV("A - O",
                                             _class="s3-grouped-checkboxes-widget-label expanded",
                                             _id="f-group-label-0"),
                                         s3_checkboxes_widget(f1,
                                                              []),
                                         DIV("T - Z",
                                             _class="s3-grouped-checkboxes-widget-label expanded",
                                             _id="f-group-label-1"),
                                         s3_checkboxes_widget(f2,
                                                              [],
                                                              start_at_id=1),
                                         _class="s3-grouped-checkboxes-widget",
                                         _name="f_widget"))))

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
        TestS3OptionsMatrixWidget,
        TestS3CheckboxesWidget,
        TestS3GroupedCheckboxesWidget,
    )

# END ========================================================================
