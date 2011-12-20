from sahanaTest import SahanaTest
import unittest
import actions

class DummyTest(SahanaTest):
    """ suite of dummy classes used for testing the test framework """
      
    _sortList = ("test_One", "test_Two")
    
    def test_One(self):
        self.assertEqual("one", "one")

    def test_Two(self):
        self.assertEqual("two", "two")

    def test_Three(self):
        self.assertEqual("three", "three")

    def test_Four(self):
        self.assertEqual("four", "four")

    def test_Five(self):
        self.assertEqual("five", "five")

    def test_Six(self):
        self.assertEqual("six", "six")

if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
