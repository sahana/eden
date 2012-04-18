# S3Search Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/s3/s3widgets.py

import unittest

from gluon import current
from s3.s3widgets import S3OptionsMatrixWidget

# =============================================================================
class TestS3OptionsMatrixWidget(unittest.TestCase):
    """
        Test the S3SearchSimpleWidget to make sure it can create queries for
        real and virtual fields.
    """

    def setUp(self):
        self.rows = (
            ("row1", "Row One"),
            ("row2", "Row Two")
        )

        self.columns = (
            ("col1", "Column One"),
            ("col2", "Column Two")
        )

        self.checklist = ('row1_col2', 'row2_col1')

    def test_widget(self):
        # Test with just the required parameters
        widget = S3OptionsMatrixWidget(self.rows, self.columns)
        expected_result = TABLE(THEAD(TR(TH(""),TH("Column One"),TH("Column Two"))),
                                TBODY(TR(TH("Row One"),
                                         TD(INPUT(_type="checkbox",
                                                  _id="id_row1_col1",
                                                  _name="row1_col1"
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _id="id_row1_col2",
                                                  _name="row1_col2"
                                                  )
                                            )
                                         ),
                                      TR(TH("Row Two"),
                                         TD(INPUT(_type="checkbox",
                                                  _id="id_row2_col1",
                                                  _name="row2_col1"
                                                  )
                                            ),
                                         TD(INPUT(_type="checkbox",
                                                  _id="id_row2_col2",
                                                  _name="row2_col2"
                                                  )
                                            )
                                         )
                                    )
                                 )
        self.failUnlessEqual(str(widget()), str(expected_result))

    def test_checklist(self):
        # Test the widget with checklist parameter
        widget = S3OptionsMatrixWidget(self.rows, self.columns, self.checklist)
        expected_result = TABLE(THEAD(TR(TH(""),TH("Column One"),TH("Column Two"))),
                                TBODY(TR(TH("Row One"),
                                         TD(INPUT(_type="checkbox",
                                                  _id="id_row1_col1",
                                                  _name="row1_col1",
                                                  )),
                                         TD(INPUT(_type="checkbox",
                                                  _id="id_row1_col2",
                                                  _name="row1_col2",
                                                  value="on"
                                                  )
                                            )
                                         ),
                                      TR(TH("Row Two"),
                                         TD(INPUT(_type="checkbox",
                                                  _id="id_row2_col1",
                                                  _name="row2_col1",
                                                  value="on"
                                                  )
                                            ),
                                         TD(INPUT(_type="checkbox",
                                                  _id="id_row2_col2",
                                                  _name="row2_col2"
                                                  )
                                            )
                                         )
                                    )
                                 )
        self.assertEqual(str(widget()), str(expected_result))


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
    )

# END ========================================================================
