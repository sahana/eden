# -*- coding: utf-8 -*-
#
# S3Navigation Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3navigation.py
#
import unittest

from s3 import S3NavigationItem as M

from unit_tests import run_suite

class SelectTests(unittest.TestCase):
    """ Tests for S3NavigationItem selection/deselection """

    # -------------------------------------------------------------------------
    def setUp(self):

        items = {
            "a1": M(tags=["a1"]),
            "a11": M(tags=["a1", "a11"]),
            "a12": M(tags=["a1", "a12"]),
            "a2": M(tags=["a2"]),
            "a21": M(tags=["a2", "a21"]),
            "a22": M(tags=["a2", "a22"]),
        }

        self.menu = M()(items["a1"](items["a11"], items["a12"]),
                        items["a2"](items["a21"], items["a22"]),
                        )
        self.items = items

    # -------------------------------------------------------------------------
    def tearDown(self):

        self.menu = None
        self.items = None

    # -------------------------------------------------------------------------
    def testSelectLeaf(self):
        """ Test selection of a leaf node """

        menu = self.menu
        items = self.items

        assertTrue = self.assertTrue
        assertIsNone = self.assertIsNone

        menu.select(tag="a11")

        assertTrue(menu.selected)
        assertTrue(items["a1"].selected)
        assertTrue(items["a11"].selected)
        assertIsNone(items["a12"].selected)
        assertIsNone(items["a2"].selected)
        assertIsNone(items["a21"].selected)
        assertIsNone(items["a22"].selected)

    # -------------------------------------------------------------------------
    def testSelectBranch(self):
        """ Test selection of a branch """

        menu = self.menu
        items = self.items

        assertTrue = self.assertTrue
        assertIsNone = self.assertIsNone

        menu.select(tag="a2")

        assertTrue(menu.selected)
        assertIsNone(items["a1"].selected)
        assertIsNone(items["a11"].selected)
        assertIsNone(items["a12"].selected)
        assertTrue(items["a2"].selected)
        assertTrue(items["a21"].selected)
        assertIsNone(items["a22"].selected)

    # -------------------------------------------------------------------------
    def testSelectSpecificNode(self):
        """ Test selection of specific nodes """

        menu = self.menu
        items = self.items

        assertTrue = self.assertTrue
        assertIsNone = self.assertIsNone

        items["a2"].select()

        assertTrue(menu.selected)
        assertIsNone(items["a1"].selected)
        assertIsNone(items["a11"].selected)
        assertIsNone(items["a12"].selected)
        assertTrue(items["a2"].selected)
        assertIsNone(items["a21"].selected)
        assertIsNone(items["a22"].selected)

        items["a12"].select()

        assertTrue(menu.selected)
        assertTrue(items["a1"].selected)
        assertIsNone(items["a11"].selected)
        assertTrue(items["a12"].selected)
        assertIsNone(items["a2"].selected)
        assertIsNone(items["a21"].selected)
        assertIsNone(items["a22"].selected)

    # -------------------------------------------------------------------------
    def testSelectNonexistentTag(self):
        """ Test selection with non-existent tag """

        menu = self.menu
        items = self.items

        assertTrue = self.assertTrue
        assertIsNone = self.assertIsNone

        # Make a selection
        menu.select(tag="a21")

        assertTrue(menu.selected)
        assertIsNone(items["a1"].selected)
        assertIsNone(items["a11"].selected)
        assertIsNone(items["a12"].selected)
        assertTrue(items["a2"].selected)
        assertTrue(items["a21"].selected)
        assertIsNone(items["a22"].selected)

        # Use a non-existent tag
        menu.select(tag="nonexistent")

        # Nothing should be selected
        assertIsNone(menu.selected)
        assertIsNone(items["a1"].selected)
        assertIsNone(items["a11"].selected)
        assertIsNone(items["a12"].selected)
        assertIsNone(items["a2"].selected)
        assertIsNone(items["a21"].selected)
        assertIsNone(items["a22"].selected)

    # -------------------------------------------------------------------------
    def testDeselectAll(self):
        """ Test deselection """

        menu = self.menu
        items = self.items

        assertTrue = self.assertTrue
        assertIsNone = self.assertIsNone

        # Make a selection
        menu.select(tag="a21")

        assertTrue(menu.selected)
        assertIsNone(items["a1"].selected)
        assertIsNone(items["a11"].selected)
        assertIsNone(items["a12"].selected)
        assertTrue(items["a2"].selected)
        assertTrue(items["a21"].selected)
        assertIsNone(items["a22"].selected)

        # Deselect all => should completely remove all selections
        menu.deselect_all()

        assertIsNone(menu.selected)
        assertIsNone(items["a1"].selected)
        assertIsNone(items["a11"].selected)
        assertIsNone(items["a12"].selected)
        assertIsNone(items["a2"].selected)
        assertIsNone(items["a21"].selected)
        assertIsNone(items["a22"].selected)

    # -------------------------------------------------------------------------
    def testSwitchSelection(self):
        """ Test consecutive manual selects """

        menu = self.menu
        items = self.items

        assertTrue = self.assertTrue
        assertIsNone = self.assertIsNone

        # First selection
        menu.select(tag="a11")

        assertTrue(menu.selected)
        assertTrue(items["a1"].selected)
        assertTrue(items["a11"].selected)
        assertIsNone(items["a12"].selected)
        assertIsNone(items["a2"].selected)
        assertIsNone(items["a21"].selected)
        assertIsNone(items["a22"].selected)

        # Second selection => should completely reset the first
        menu.select(tag="a22")

        assertTrue(menu.selected)
        assertIsNone(items["a1"].selected)
        assertIsNone(items["a11"].selected)
        assertIsNone(items["a12"].selected)
        assertTrue(items["a2"].selected)
        assertIsNone(items["a21"].selected)
        assertTrue(items["a22"].selected)

# =============================================================================
if __name__ == "__main__":

    run_suite(
        SelectTests,
    )

# END ========================================================================
