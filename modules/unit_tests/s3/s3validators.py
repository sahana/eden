# -*- coding: utf-8 -*-
#
# Validators Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/s3/s3validators.py
#
import unittest
from gluon.dal import Query

# =============================================================================
class ISLatTest(unittest.TestCase):
    """
        Latitude has to be in decimal degrees between -90 & 90
        - we can convert D/M/S or D°M'S" format into decimal degrees:
        Zero padded, separated by spaces or : or (d, m, s) or (°, ', ") or run together and followed by cardinal direction initial (N,S) Note: Only seconds can have decimals places. A decimal point with no trailing digits is invalid.
        Matches	
        40:26:46N | 40°26'47?N | 40d 26m 47s N | 90 00 00.0 | 89 59 50.4141 S | 00 00 00.0
        Non-Matches	
        90 00 00.001 N | 9 00 00.00 N | 9 00 00.00 | 90 61 50.4121 S | -90 48 50. N | 90 00 00. N | 00 00 00.
    """

    pass

# =============================================================================
class ISLonTest(unittest.TestCase):
    """
        Longitude has to be in decimal degrees between -180 & 180
        - we can convert D/M/S format into decimal degrees
        Zero padded, separated by spaces or : or (d, m, s) or (°, ', ") or run together and followed by cardinal direction initial (E,W) Note: Only seconds can have decimals places. A decimal point with no trailing digits is invalid.
        Matches	
        079:56:55W | 079°58'36?W | 079d 58' 36? W | 180 00 00.0 | 090 29 20.4 E | 000 00 00.0
        Non-Matches	
        180 00 00.001 E | 79 00 00.00 E | -79 00 00.00 | 090 29 20.4 E | -090 29 20.4 E | 180 00 00. E | 000 00 00.
    """

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
        ISLatTest,
        ISLonTest,
    )

# END ========================================================================
