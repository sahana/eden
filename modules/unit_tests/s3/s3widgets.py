# S3 Widgets Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3widgets.py

import unittest

from collections import OrderedDict

from gluon import *
from gluon.storage import Storage

from s3.s3widgets import S3OptionsMatrixWidget

from unit_tests import run_suite

# =============================================================================
class TestS3OptionsMatrixWidget(unittest.TestCase):
    """ Test the S3OptionsMatrixWidget widget for correct output """

    # @todo: deprecate?

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

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
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
if __name__ == "__main__":

    run_suite(
        TestS3OptionsMatrixWidget,
    )

# END ========================================================================
