
# this gets ported to javascript in s3.gis.climate.js
# look for "sensible"

import math
def sensible_range(min_value, max_value, significant_digits = 2):
    assert min_value < max_value
    def scaling_factor(value):
        # power of 10 to use to get correct precision
        return 10.0**(
            math.floor(math.log(abs(value), 10)) - (significant_digits - 1)
        )
    def sensible(value, round):
        if value == 0.0:
            return 0.0
        else:
            factor = scaling_factor(value)
            return round(value/factor) * factor
    range_mag = scaling_factor(
        sensible(max_value, math.ceil) - sensible(min_value, math.floor)
    )
    return (math.floor(min_value/range_mag) * range_mag,
        math.ceil(max_value/range_mag) * range_mag)

import unittest
class TestSensibleRange(unittest.TestCase):
    def sensible_range(test, args, (expected_lower_limit, expected_upper_limit)):
        (actual_lower_limit, actual_upper_limit) = sensible_range(*args)
        test.assertAlmostEquals(actual_lower_limit, expected_lower_limit)
        test.assertAlmostEquals(actual_upper_limit, expected_upper_limit)
        
    def test_1(test):
        test.sensible_range((-1234, 0.1, 2), (-1300.0, 100.0))
        
    def test_2(test):
        test.sensible_range((0.05, 0.1, 2), (0.05, 0.1))
        
    def test_3(test):
        test.sensible_range((0.0512, 0.1, 2), (0.051, 0.1))
        
    def test_4(test):
        test.sensible_range((-0.1, 0.0512, 2), (-0.1, 0.06))
        
    def test_0_sd(test):
        test.sensible_range((-0.1, 0.0512, 0), (-10.0, 10.0))
        
    def test_both_negative(test):
        test.sensible_range((-15765, -0.001, 2), (-16000.0, 0.0))
        
    def test_bad_range(test):
        test.assertRaises(AssertionError, sensible_range, 0.0, 0.0, 2)
        test.assertRaises(AssertionError, sensible_range, -0.0, 0.0, 2)
        test.assertRaises(AssertionError, sensible_range, 0.0, -0.0, 2)
        test.assertRaises(AssertionError, sensible_range, 10, -10000, 2)

suite = unittest.TestLoader().loadTestsFromTestCase(TestSensibleRange)
unittest.TextTestRunner(verbosity=2).run(suite)
