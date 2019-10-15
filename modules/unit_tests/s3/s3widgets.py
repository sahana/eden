# S3 Widgets Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3widgets.py

import unittest

from collections import OrderedDict

from gluon import *
from gluon.storage import Storage

from s3.s3widgets import S3HoursWidget, S3LocationSelector, S3OptionsMatrixWidget

from unit_tests import run_suite

# =============================================================================
class S3OptionsMatrixWidgetTests(unittest.TestCase):
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
        self.assertEqual(str(self.widget(self.field, [])), str(expected_result))

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
class S3HoursWidgetTests(unittest.TestCase):
    """ Tests for S3HoursWidget """

    # -------------------------------------------------------------------------
    def test_parse(self):
        """ Test parsing of regular hours-values """

        assertEqual = self.assertEqual

        w = S3HoursWidget(interval=None,
                          precision=None,
                          explicit_above=None,
                          )
        parse = w.s3_parse

        samples = {"0": 0.0,              # decimal
                   "0.28754": 0.28754,    # decimal
                   "6:30": 6.5,           # colon-notation HH:MM
                   "3:45:36": 3.76,       # colon-notation, with seconds
                   "12:36.75": 12.6125,   # colon-notation, with fraction
                   "1h15min": 1.25,       # unit-notation
                   "9h18s": 9.005,        # unit-notation without minutes segment
                   }

        for s in samples.items():
            hours = parse(s[0])
            assertEqual(round(hours, 8), s[1], "'%s' recognized as %s, expected %s" % (s[0], hours, s[1]))

    # -------------------------------------------------------------------------
    def test_parse_rounded(self):
        """ Test parsing of regular hours-values, with rounding """

        assertEqual = self.assertEqual

        w = S3HoursWidget(interval=None,
                          precision=2,
                          explicit_above=None,
                          )
        parse = w.s3_parse

        samples = {"18": 18.0,          # decimal, hours assumed
                   "18m": 0.3,          # decimal, explicit unit
                   "0.28754": 0.29,     # decimal, hours assumed
                   "3,4": 3.4,          # decimal, hours assumed, comma tolerated
                   "6:30": 6.5,         # colon-notation, hours assumed
                   "3:45:36": 3.76,     # colon-notation, with seconds
                   "12:36.75m": 0.21,   # colon-notation, explicit unit
                   "1h15min": 1.25,     # unit-notation
                   "9h18s": 9.01,       # unit-notation without minutes
                   }

        for s in samples.items():
            hours = parse(s[0])
            assertEqual(round(hours, 8), s[1], "'%s' recognized as %s, expected %s" % (s[0], hours, s[1]))

    # -------------------------------------------------------------------------
    def test_parse_interval(self):
        """ Test parsing of regular hours-values, rounded up to minutes interval """

        assertEqual = self.assertEqual

        w = S3HoursWidget(interval=15, # Round to 1/4 hours
                          precision=None,
                          explicit_above=None,
                          )
        parse = w.s3_parse

        samples = {"0": 0.0,
                   "0.28754": 0.5,
                   "6:30": 6.5,
                   "3:45:36": 4.0,
                   "1h15min": 1.25,
                   "9h18s": 9.25,
                   }

        for s in samples.items():
            hours = parse(s[0])
            assertEqual(round(hours, 8), s[1], "'%s' recognized as %s, expected %s" % (s[0], hours, s[1]))

    # -------------------------------------------------------------------------
    def test_validate_implied_unit_limit(self):
        """ Test in-widget validation of explicit notation above limit """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual

        w = S3HoursWidget(interval=None,
                          precision=2,
                          explicit_above=4,
                          )
        validate = w.validate

        samples = {"3": 3.0,        # lacks unit but below limit, hours assumed
                   "0.28754": 0.29, # lacks unit but below limit, hours assumed
                   "6:30": 6.5,     # lacks unit and above limit, but tolerated for colon-notation
                   "3:45:36": 3.76, # lacks unit and above limit, but tolerated for colon-notation
                   "6:18m": 0.11,   # Colon-notation with explicit unit, overriding assumption
                   "1h15min": 1.25, # Explicit unit
                   "9h18s": 9.01,   # Explicit unit
                   "4.95": "error", # lacks unit and above limit => ambiguous
                   "3h15": "error", # 15 segment lacks unit and above limit => edge-case, treated as ambiguous
                   }

        for s in samples.items():
            hours, error = validate(s[0])

            if s[1] == "error":
                assertNotEqual(error, None)
            else:
                assertEqual(error, None)
                assertEqual(round(hours, 8), s[1], "'%s' recognized as %s, expected %s" % (s[0], hours, s[1]))

# =============================================================================
class S3LocationSelectorTests(unittest.TestCase):
    """ Tests for S3LocationSelector """

    # -------------------------------------------------------------------------
    def test_empty_labels(self):
        """ Test _labels when there aren't any locations """

        location_selector = S3LocationSelector()
        levels = ['L0', 'L1', 'L2', 'L3', 'L4', 'L5']
        results = location_selector._labels(levels, country=None)
        self.assertEqual(results[0], {'L0': current.T('Country')})
        self.assertEqual(results[1], {})

# =============================================================================
if __name__ == "__main__":

    run_suite(
        S3OptionsMatrixWidgetTests,
        S3HoursWidgetTests,
        S3LocationSelectorTests,
    )

# END ========================================================================
