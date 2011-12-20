
import unittest

class Test_s3mgr_raises_on_nonexistent_modules(unittest.TestCase):
    def test(test):
        test.assertRaises(Exception, s3mgr.load, "something that doesn't exist")
