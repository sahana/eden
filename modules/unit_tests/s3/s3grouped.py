# -*- coding: utf-8 -*-
#
# S3GroupedItems Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3grouped.py
#
import unittest

from s3.s3grouped import S3GroupedItems, S3GroupAggregate

# =============================================================================
class S3GroupedItemsTests(unittest.TestCase):
    """ Tests for grouped items """

    # -------------------------------------------------------------------------
    def testNoGrouping(self):
        """ Test S3GroupedItems behavior without grouping axis """

        assertEqual = self.assertEqual

        items = [
            {"name": "Item1", "type": "A"},
            {"name": "Item2", "type": "C"},
            {"name": "Item3", "type": "D"},
            {"name": "Item4", "type": "B"},
            {"name": "Item5", "type": "A"},
            {"name": "Item6", "type": "D"},
            {"name": "Item7", "type": "E"},
        ]

        # Generate grouped items instance without grouping axis
        gi = S3GroupedItems(items)

        # Should have no subgroups
        assertEqual(len(list(gi.groups)), 0)

        # All items should be in top-level group, and in original order
        for index, item in enumerate(gi.items):
            assertEqual(item["name"], items[index]["name"])

    # -------------------------------------------------------------------------
    def testSingleAxisGrouping(self):
        """
            Verify that S3GroupedItems accepts single axis-parameter,
            and retains the original order of groups
        """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue
        assertIn = self.assertIn

        items = [
            {"name": "Item1", "type": "A"},
            {"name": "Item2", "type": ["C", "D"]},
            {"name": "Item3", "type": "D"},
            {"name": "Item4", "type": "B"},
            {"name": "Item5", "type": "A"},
            {"name": "Item6", "type": "D"},
            {"name": "Item7", "type": "E"},
        ]

        # The original order of types in the items (=order of first appearance)
        types = ["A", "C", "D", "B", "E"]

        gi = S3GroupedItems(items, groupby="type")

        # Order of groups should match the original order
        for g, group in enumerate(gi.groups):
            assertEqual(group["type"], types[g])

            group_items = group.items
            if not group_items:
                continue

            last = len(group_items) - 1
            for i, item in enumerate(group_items):
                # Verify that the item belongs into this group
                value = item["type"]
                if type(value) is list:
                    assertIn(group["type"], value)
                else:
                    assertEqual(group["type"], value)

                # Order of group items should match their original order
                if i < last:
                    assertTrue(item["name"] < group_items[i + 1]["name"])

    # -------------------------------------------------------------------------
    def testMultiAxisGrouping(self):
        """ Verify S3GroupedItems behavior for multiple grouping axes """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        items = [
            {"name": "Item1", "t1": "A", "t2": "1", "t3": "X"},
            {"name": "Item2", "t1": "B", "t2": "2", "t3": "Y"},
            {"name": "Item3", "t1": "C", "t2": "3", "t3": "X"},
            {"name": "Item4", "t1": "A", "t2": "3", "t3": "Z"},
            {"name": "Item5", "t1": "C", "t2": "2", "t3": "X"},
            {"name": "Item6", "t1": "D", "t2": "2", "t3": "X"},
        ]

        axes = ["t1", "t2", "t3"]

        gi = S3GroupedItems(items, groupby=axes)

        group = gi
        for depth, axis in enumerate(axes):

            # Grouping happens in order of appearance of keys
            assertEqual(axes[depth], group.key)

            # All keys produce subgroups
            subgroups = list(group.groups)
            assertTrue(len(subgroups) > 0)

            group = subgroups[0]

        # Deepest level should have no further subgroups
        assertEqual(len(list(group.groups)), 0)

    # -------------------------------------------------------------------------
    def testRawValuePrecedence(self):
        """
            Verify that raw values are preferred for grouping,
            including fallbacks for missing raw data or invalid type
        """

        assertEqual = self.assertEqual

        items = [
            {"name": "Item1", "type": "A", "_row": {"name": "Item1", "type": "X"}},
            {"name": "Item2", "type": "C", "_row": {"name": "Item2", "type": "Y"}},
            {"name": "Item3", "type": "D", "_row": {"name": "Item3", "type": "Z"}},
            {"name": "Item4", "type": "B", "_row": "test"},
            {"name": "Item5", "type": "A", "_row": {"name": "Item5", "type": "X"}},
            {"name": "Item6", "type": "D", "_row": {"name": "Item6", "type": "Z"}},
            {"name": "Item7", "type": "E"},
        ]

        # The original order of types in the items (=order of first appearance)
        types = ["X", "Y", "Z", "B", "E"]

        gi = S3GroupedItems(items, groupby=["type"])

        # Order of groups should match the original order
        for index, group in enumerate(gi.groups):
            assertEqual(group["type"], types[index])

    # -------------------------------------------------------------------------
    def testGetValues(self):
        """ Test get_values method """

        assertIn = self.assertIn

        items = [
            {"name": "Item1"},
            {"name": "Item2"},
            {"name": "Item3"},
            {"name": "Item4"},
            {"name": "Item5"},
            {"name": "Item6"},
            {"name": "Item7"},
        ]

        gi = S3GroupedItems(items)
        values = gi.get_values("name")

        for item in items:
            assertIn(item["name"], values)

    # -------------------------------------------------------------------------
    def testAggregate(self):
        """ Test aggregation """

        assertIn = self.assertIn
        assertEqual = self.assertEqual

        items = [
            {"name": "Item1", "type": "A", "value": 2.6},
            {"name": "Item2", "type": "C", "value": 4.9},
            {"name": "Item3", "type": "D", "value": 7.2},
            {"name": "Item4", "type": "B", "value": 1.5},
            {"name": "Item5", "type": "A", "value": 9.4},
            {"name": "Item6", "type": "D", "value": 6.1},
            {"name": "Item7", "type": "E", "value": 3.5},
        ]

        results = {"A": 12.0, "B": 1.5, "C": 4.9, "D": 13.3, "E": 3.5}

        gi = S3GroupedItems(items, groupby="type")

        # Verify top-level aggregate
        aggregate = gi.aggregate("sum", "value")
        assertEqual(aggregate.result, 35.2)

        # Verify per-group aggregates
        for group in gi.groups:
            t = group["type"]
            assertIn(("sum", "value"), group._aggregates)
            assertEqual(group[("sum", "value")], results[t])

    # -------------------------------------------------------------------------
    def testConstructionWithAggregate(self):
        """ Test aggregation during construction """

        assertIn = self.assertIn
        assertEqual = self.assertEqual

        items = [
            {"name": "Item1", "type": "A", "value": 2.6},
            {"name": "Item2", "type": "C", "value": 4.9},
            {"name": "Item3", "type": "D", "value": 7.2},
            {"name": "Item4", "type": "B", "value": 1.5},
            {"name": "Item5", "type": "A", "value": 9.4},
            {"name": "Item6", "type": "D", "value": 6.1},
            {"name": "Item7", "type": "E", "value": 3.5},
        ]

        results = {"A": 12.0, "B": 1.5, "C": 4.9, "D": 13.3, "E": 3.5}

        # Test single aggregate
        gi = S3GroupedItems(items,
                            groupby = "type",
                            aggregate = ("sum", "value"),
                            )

        # Verify top-level aggregate
        assertIn(("sum", "value"), gi._aggregates)
        result = gi[("sum", "value")]
        assertEqual(result, 35.2)

        # Verify per-group aggregates
        for group in gi.groups:
            t = group["type"]
            assertIn(("sum", "value"), group._aggregates)
            assertEqual(group[("sum", "value")], results[t])

        # Test multiple aggregates
        gi = S3GroupedItems(items,
                            groupby = "type",
                            aggregate = [("min", "value"),
                                         ("max", "value"),
                                         ("sum", "nonexistent")
                                         ],
                            )

        # Verify top-level aggregates
        assertIn(("min", "value"), gi._aggregates)
        assertIn(("max", "value"), gi._aggregates)
        assertIn(("sum", "nonexistent"), gi._aggregates)
        result = gi[("min", "value")]
        assertEqual(result, 1.5)
        result = gi[("max", "value")]
        assertEqual(result, 9.4)
        result = gi[("sum", "nonexistent")]
        assertEqual(result, 0.0)

        # Verify per-group aggregates
        results = {"A": 2.6, "B": 1.5, "C": 4.9, "D": 6.1, "E": 3.5}
        for group in gi.groups:
            t = group["type"]
            assertIn(("min", "value"), group._aggregates)
            assertEqual(group[("min", "value")], results[t])

        results = {"A": 9.4, "B": 1.5, "C": 4.9, "D": 7.2, "E": 3.5}
        for group in gi.groups:
            t = group["type"]
            assertIn(("max", "value"), group._aggregates)
            assertEqual(group[("max", "value")], results[t])

        for group in gi.groups:
            assertIn(("sum", "nonexistent"), group._aggregates)
            assertEqual(group[("sum", "nonexistent")], 0.0)

# =============================================================================
class S3GroupAggregateTests(unittest.TestCase):
    """ Tests for grouped items value aggregation methods """

    # -------------------------------------------------------------------------
    def testCount(self):
        """ Test aggregation method 'count' """

        assertEqual = self.assertEqual

        # Regular input
        values = ["A", "B", "B", "C"]
        aggregate = S3GroupAggregate("count", "Example", values)
        assertEqual(aggregate.result, 3)

        # None gives always None
        values = None
        aggregate = S3GroupAggregate("count", "Example", values)
        assertEqual(aggregate.result, None)

        # Invalid input: non-iterable type
        values = 17
        aggregate = S3GroupAggregate("count", "Example", values)
        assertEqual(aggregate.result, None)

    # -------------------------------------------------------------------------
    def testSum(self):
        """ Test aggregation method 'sum' """

        assertEqual = self.assertEqual

        # Regular input
        values = [2, 1.7, 3, 1]
        aggregate = S3GroupAggregate("sum", "Example", values)
        assertEqual(aggregate.result, 7.7)

        # Empty input
        values = []
        aggregate = S3GroupAggregate("sum", "Example", values)
        assertEqual(aggregate.result, 0.0)

        # Non-numeric type (e.g. returned from virtual fields)
        values = ["1", "other"]
        aggregate = S3GroupAggregate("sum", "Example", values)
        assertEqual(aggregate.result, 0.0)

        # None gives always None
        values = None
        aggregate = S3GroupAggregate("sum", "Example", values)
        assertEqual(aggregate.result, None)

    # -------------------------------------------------------------------------
    def testMin(self):
        """ Test aggregation method 'min' """

        assertEqual = self.assertEqual

        # Regular input
        values = [2, 1.7, 3, 1]
        aggregate = S3GroupAggregate("min", "Example", values)
        assertEqual(aggregate.result, 1)

        # None gives always None
        values = None
        aggregate = S3GroupAggregate("min", "Example", values)
        assertEqual(aggregate.result, None)

        # Invalid input: non-iterable
        values = 45
        aggregate = S3GroupAggregate("min", "Example", values)
        assertEqual(aggregate.result, None)

    # -------------------------------------------------------------------------
    def testMax(self):
        """ Test aggregation method 'max' """

        assertEqual = self.assertEqual

        # Regular input
        values = [2, 1.7, 3, 1]
        aggregate = S3GroupAggregate("max", "Example", values)
        assertEqual(aggregate.result, 3)

        # None gives always None
        values = None
        aggregate = S3GroupAggregate("max", "Example", values)
        assertEqual(aggregate.result, None)

        # Invalid input: non-iterable
        values = lambda: None
        aggregate = S3GroupAggregate("max", "Example", values)
        assertEqual(aggregate.result, None)

    # -------------------------------------------------------------------------
    def testAvg(self):
        """ Test aggregation method 'avg' """

        assertEqual = self.assertEqual

        # Regular input
        values = [2, 1.7, 3, 1]
        aggregate = S3GroupAggregate("avg", "Example", values)
        assertEqual(aggregate.result, 1.925)

        # None gives always None
        values = None
        aggregate = S3GroupAggregate("avg", "Example", values)
        assertEqual(aggregate.result, None)

        # Invalid input: non-numeric type
        values = ["1", "other"]
        aggregate = S3GroupAggregate("avg", "Example", values)
        assertEqual(aggregate.result, None)

    # -------------------------------------------------------------------------
    def testAggregate(self):
        """ Test aggregation of aggregates """

        assertTrue = self.assertTrue
        assertEqual = self.assertEqual
        assertRaises = self.assertRaises

        # Create two aggregates
        values1 = [2, 4, 6, 12]
        ga1 = S3GroupAggregate("avg", "Example", values1)
        assertEqual(ga1.result, 6.0)

        values2 = [5, 3, 9, 8]
        ga2 = S3GroupAggregate("avg", "Example", values2)
        assertEqual(ga2.result, 6.25)

        # Combine the two aggregates
        ga = S3GroupAggregate.aggregate((ga1, ga2))
        assertEqual(ga.result, 6.125)
        for value in values1 + values2:
            assertTrue(value in ga.values)

        # Combine with method mismatch
        ga = S3GroupAggregate("min", "Example", values1)
        with assertRaises(TypeError):
            S3GroupAggregate((ga1, ga2, ga))

        # Combine with key mismatch
        ga = S3GroupAggregate("avg", "Other", values1)
        with assertRaises(TypeError):
            S3GroupAggregate((ga1, ga2, ga))

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
        S3GroupedItemsTests,
        S3GroupAggregateTests,
    )

# END ========================================================================
