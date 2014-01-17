# -*- coding: utf-8 -*-
#
# Utils Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/s3/s3timeplot.py
#
import datetime
import random
import unittest

from s3.s3timeplot import *

# =============================================================================
class EventTests(unittest.TestCase):

    # -------------------------------------------------------------------------
    def testConstruction(self):
        """ Test event construction """

        dt = datetime.datetime
        start = dt(2004, 1, 1)
        end = dt(2004, 3, 21)

        event_id = 1
        event_type = "test"
        values = {"test": 2}

        event = S3TimePlotEvent(event_id,
                                start=start,
                                end=end)

        self.assertEqual(event.event_id, event_id)
        self.assertEqual(event.event_type, None)
        self.assertTrue(isinstance(event.values, dict))
        self.assertEqual(event["test"], None)

        event = S3TimePlotEvent(event_id,
                                start=start,
                                end=end,
                                values=values)

        self.assertEqual(event.event_id, event_id)
        self.assertEqual(event.event_type, None)
        self.assertEqual(event.values, values)
        self.assertEqual(event["test"], 2)

        event = S3TimePlotEvent(event_id,
                                start=start,
                                end=end,
                                values=values,
                                event_type=event_type)

        self.assertEqual(event.event_id, event_id)
        self.assertEqual(event.event_type, event_type)
        self.assertEqual(event.values, values)
        self.assertEqual(event["test"], 2)


# =============================================================================
class PeriodTests(unittest.TestCase):

    def setUp(self):

        dt = datetime.datetime
        start = dt(2013,4,1)
        end = dt(2013,7,1)

        period = S3TimePlotPeriod(start=start, end=end)
        events = [
            (2, (2013,4,1), (2013,4,21), {"test3": 6.2, "test4": [31]}, "B"),
            (6, (2013,4,14), (2013,5,7), {"test3": 8.1, "test4": [37, 91]}, "B"),
            (8, (2013,1,12), (2013,9,19), None, "B"),
            (1, (2013,4,1), (2013,4,21), {"test1": 2, "test2": [13]}, "A"),
            (2, (2013,4,14), (2013,5,7), {"test1": 3, "test2": [17, 21]}, "A"),
            (3, (2013,4,21), (2013,6,3), {"test1": 1, "test2": [14, None, 11]}, "A"),
            (4, (2013,4,18), (2013,5,27), {"test1": 9}, "A"),
        ]
        for event_id, start, end, values, event_type in events:
            event = S3TimePlotEvent(event_id,
                                    start=dt(*start),
                                    end=dt(*end),
                                    values=values,
                                    event_type=event_type)
            period.add(event)
        self.period = period

    # -------------------------------------------------------------------------
    def testAdd(self):
        """ Test adding of events to a period """

        period = self.period
        
        self.assertTrue("A" in period.sets)
        self.assertTrue("B" in period.sets)
        self.assertEqual(len(period.sets), 2)

        set_A = period.sets["A"]
        self.assertEqual(len(set_A), 4)
        set_B = period.sets["B"]
        self.assertEqual(len(set_B), 3)

    # -------------------------------------------------------------------------
    def testAggregateCount(self):
        """ Test count aggregation method """

        period = self.period

        # Test set A
        value = period.aggregate(method="count", event_type="A")
        self.assertEqual(value, 4)
        value = period.aggregate(method="count", event_type="A", field="test1")
        self.assertEqual(value, 4)
        value = period.aggregate(method="count", event_type="A", field="test2")
        self.assertEqual(value, 5)

        # Test set B
        value = period.aggregate(method="count", event_type="B", field="test1")
        self.assertEqual(value, 0)
        value = period.aggregate(method="count", event_type="B", field="test3")
        self.assertEqual(value, 2)
        value = period.aggregate(method="count", event_type="B", field="test4")
        self.assertEqual(value, 3)

        # Test with nonexistent set
        value = period.aggregate(method="count",
                                 event_type="nonexistent", field="test1")
        self.assertEqual(value, 0)

        # Test with unspecified set
        value = period.aggregate(method="count", field="test1")
        self.assertEqual(value, 0)

    # -------------------------------------------------------------------------
    def testAggregateSum(self):
        """ Test sum aggregation method """
        
        period = self.period

        # Test set A
        value = period.aggregate(method="sum", event_type="A")
        self.assertEqual(value, None)
        value = period.aggregate(method="sum", event_type="A", field="test1")
        self.assertEqual(value, 15)
        value = period.aggregate(method="sum", event_type="A", field="test2")
        self.assertEqual(value, 76)

        # Test set B
        value = period.aggregate(method="sum", event_type="B", field="test1")
        self.assertEqual(value, 0)
        value = period.aggregate(method="sum", event_type="B", field="test3")
        self.assertEqual(value, 14.3)
        value = period.aggregate(method="sum", event_type="B", field="test4")
        self.assertEqual(value, 159)

        # Test with nonexistent set
        value = period.aggregate(method="sum",
                                 event_type="nonexistent", field="test1")
        self.assertEqual(value, 0)

        # Test with unspecified set
        value = period.aggregate(method="sum", field="test1")
        self.assertEqual(value, 0)

    # -------------------------------------------------------------------------
    def testAggregateAvg(self):
        """ Test avg aggregation method """

        period = self.period

        # Test set A
        value = period.aggregate(method="avg", event_type="A")
        self.assertEqual(value, None)
        value = period.aggregate(method="avg", event_type="A", field="test1")
        self.assertEqual(value, 3.75)
        value = period.aggregate(method="avg", event_type="A", field="test2")
        self.assertEqual(value, 15.2)

        # Test set B
        value = period.aggregate(method="avg", event_type="B", field="test1")
        self.assertEqual(value, None)
        value = period.aggregate(method="avg", event_type="B", field="test3")
        self.assertEqual(value, 7.15)
        value = period.aggregate(method="avg", event_type="B", field="test4")
        self.assertEqual(value, 53.0)

        # Test with nonexistent set
        value = period.aggregate(method="avg",
                                 event_type="nonexistent", field="test1")
        self.assertEqual(value, None)

        # Test with unspecified set
        value = period.aggregate(method="avg", field="test1")
        self.assertEqual(value, None)

    # -------------------------------------------------------------------------
    def testAggregateMin(self):
        """ Test min aggregation method """

        period = self.period

        # Test set A
        value = period.aggregate(method="min", event_type="A")
        self.assertEqual(value, None)
        value = period.aggregate(method="min", event_type="A", field="test1")
        self.assertEqual(value, 1)
        value = period.aggregate(method="min", event_type="A", field="test2")
        self.assertEqual(value, 11)

        # Test set B
        value = period.aggregate(method="min", event_type="B", field="test1")
        self.assertEqual(value, None)
        value = period.aggregate(method="min", event_type="B", field="test3")
        self.assertEqual(value, 6.2)
        value = period.aggregate(method="min", event_type="B", field="test4")
        self.assertEqual(value, 31)

        # Test with nonexistent set
        value = period.aggregate(method="min",
                                 event_type="nonexistent", field="test1")
        self.assertEqual(value, None)

        # Test with unspecified set
        value = period.aggregate(method="min", field="test1")
        self.assertEqual(value, None)

    # -------------------------------------------------------------------------
    def testAggregateMax(self):
        """ Test max aggregation method """

        period = self.period

        # Test set A
        value = period.aggregate(method="max", event_type="A")
        self.assertEqual(value, None)
        value = period.aggregate(method="max", event_type="A", field="test1")
        self.assertEqual(value, 9)
        value = period.aggregate(method="max", event_type="A", field="test2")
        self.assertEqual(value, 21)

        # Test set B
        value = period.aggregate(method="max", event_type="B", field="test1")
        self.assertEqual(value, None)
        value = period.aggregate(method="max", event_type="B", field="test3")
        self.assertEqual(value, 8.1)
        value = period.aggregate(method="max", event_type="B", field="test4")
        self.assertEqual(value, 91)

        # Test with nonexistent set
        value = period.aggregate(method="max",
                                 event_type="nonexistent", field="test1")
        self.assertEqual(value, None)
        
        # Test with unspecified set
        value = period.aggregate(method="max", field="test1")
        self.assertEqual(value, None)
        
    # -------------------------------------------------------------------------
    def testEvents(self):
        """ Test access to events in a period """

        period = self.period

        # Test set A
        events = period.events(event_type="A")
        self.assertTrue(isinstance(events, list))
        self.assertEqual(len(events), 4)
        event_ids = set([1, 2, 3, 4])
        for event in events:
            self.assertEqual(event.event_type, "A")
            event_ids.discard(event.event_id)
        self.assertEqual(len(event_ids), 0)

        # Test set B
        events = period.events(event_type="B")
        self.assertTrue(isinstance(events, list))
        self.assertEqual(len(events), 3)
        event_ids = set([2, 6, 8])
        for event in events:
            self.assertEqual(event.event_type, "B")
            event_ids.discard(event.event_id)
        self.assertEqual(len(event_ids), 0)

        # Test with nonexistent set
        events = period.events("nonexistent")
        self.assertEqual(events, [])

        # Test with unspecified set
        events = period.events()
        self.assertEqual(events, [])

    # -------------------------------------------------------------------------
    def testCount(self):
        """ Test counting of events in a period """
        
        period = self.period

        # Test set A
        num = period.count("A")
        self.assertEqual(num, 4)

        # Test set B
        num = period.count("B")
        self.assertEqual(num, 3)

        # Test nonexistent set
        num = period.count("nonexistent")
        self.assertEqual(num, 0)

        # Test unspecified set
        num = period.count()
        self.assertEqual(num, 0)

# =============================================================================
class EventFrameTests(unittest.TestCase):

    def setUp(self):

        dt = datetime.datetime
        
        data = [
            # Always
            (1, None, None, {"test": 2}, "A"),
            # First two quarters
            (2, None, (2012,6,19), {"test": 5}, "A"),
            # Last three quarters
            (3, (2012,5,1), None, {"test": 8}, "A"),
            # First and Second Quarter
            (4, (2012,1,14), (2012,5,7), {"test": 3}, "A"),
            # Second and Third Quarter
            (5, (2012,5,1), (2012,7,21), {"test": 2}, "A"),
            # Third and Fourth Quarter
            (6, (2012,8,8), (2012,11,3), {"test": 1}, "A"),
            # Only Fourth Quarter
            (7, (2012,10,18), (2013,5,27), {"test": 9}, "A"),
            # Ended before Event Frame
            (8, (2011,1,1), (2011,12,6), {"test": 9}, "A"),
            # Starting after Event Frame
            (9, (2013,1,18), (2013,5,27), {"test": 3}, "A"),
        ]
        
        events = []
        for event_id, start, end, values, event_type in data:
            events.append(S3TimePlotEvent(event_id,
                                          start=dt(*start) if start else None,
                                          end=dt(*end) if end else None,
                                          values=values,
                                          event_type=event_type))
        self.events = events

    # -------------------------------------------------------------------------
    def testExtend(self):
        """ Test correct grouping of events into intervals """

        dt = datetime.datetime

        # Create event frame and add events
        ef = S3TimePlotEventFrame(dt(2012,1,1),
                                  dt(2012,12,15),
                                  slots="3 months")
        ef.extend(self.events)

        # Expected result
        expected = [
            ((2012, 1, 1), (2012, 4, 1), [1, 2, 4], (10, 5)),
            ((2012, 4, 1), (2012, 7, 1), [1, 2, 3, 4, 5], (20, 8)),
            ((2012, 7, 1), (2012, 10, 1), [1, 3, 5, 6], (13, 8)),
            ((2012, 10, 1), (2012, 12, 15), [1, 3, 6, 7], (20, 9)),
        ]

        # Check
        assertEqual = self.assertEqual
        for i, period in enumerate(ef):
            start, end, expected_ids, expected_result = expected[i]

            # Check start/end date of period
            assertEqual(period.start, dt(*start))
            assertEqual(period.end, dt(*end))

            # Check events in period
            event_ids = [event.event_id for event in period.events("A")]
            assertEqual(set(event_ids), set(expected_ids))

            # Check aggregation
            result = period.aggregate("sum", field="test", event_type="A")
            assertEqual(result, expected_result[0])
            
            result = period.aggregate("max", field="test", event_type="A")
            assertEqual(result, expected_result[1])

    # -------------------------------------------------------------------------
    def testPeriodsDays(self):
        """ Test iteration over periods (days) """

        dt = datetime.datetime

        ef = S3TimePlotEventFrame(dt(2011, 1, 5),
                                  dt(2011, 1, 8),
                                  slots="days")
        expected = [(dt(2011, 1, 5), dt(2011, 1, 6)),
                    (dt(2011, 1, 6), dt(2011, 1, 7)),
                    (dt(2011, 1, 7), dt(2011, 1, 8))]
        for i, period in enumerate(ef):
            self.assertEqual(period.start, expected[i][0])
            self.assertEqual(period.end, expected[i][1])

        ef = S3TimePlotEventFrame(dt(2011, 1, 5),
                                  dt(2011, 1, 16),
                                  slots="4 days")
        expected = [(dt(2011, 1, 5), dt(2011, 1, 9)),
                    (dt(2011, 1, 9), dt(2011, 1, 13)),
                    (dt(2011, 1, 13), dt(2011, 1, 16))]
        for i, period in enumerate(ef):
            self.assertEqual(period.start, expected[i][0])
            self.assertEqual(period.end, expected[i][1])

    # -------------------------------------------------------------------------
    def testPeriodsWeeks(self):
        """ Test iteration over periods (weeks) """

        dt = datetime.datetime

        ef = S3TimePlotEventFrame(dt(2011, 1, 5),
                                  dt(2011, 1, 28),
                                  slots="weeks")
        expected = [(dt(2011, 1, 5), dt(2011, 1, 12)),
                    (dt(2011, 1, 12), dt(2011, 1, 19)),
                    (dt(2011, 1, 19), dt(2011, 1, 26)),
                    (dt(2011, 1, 26), dt(2011, 1, 28))]
        for i, period in enumerate(ef):
            self.assertEqual(period.start, expected[i][0])
            self.assertEqual(period.end, expected[i][1])

        ef = S3TimePlotEventFrame(dt(2011, 1, 5),
                                  dt(2011, 2, 16),
                                  slots="2 weeks")
        expected = [(dt(2011, 1, 5), dt(2011, 1, 19)),
                    (dt(2011, 1, 19), dt(2011, 2, 2)),
                    (dt(2011, 2, 2), dt(2011, 2, 16))]
        for i, period in enumerate(ef):
            self.assertEqual(period.start, expected[i][0])
            self.assertEqual(period.end, expected[i][1])
            
    # -------------------------------------------------------------------------
    def testPeriodsMonths(self):
        """ Test iteration over periods (months) """

        dt = datetime.datetime

        ef = S3TimePlotEventFrame(dt(2011, 1, 5),
                                  dt(2011, 4, 28),
                                  slots="months")
        expected = [(dt(2011, 1, 5), dt(2011, 2, 5)),
                    (dt(2011, 2, 5), dt(2011, 3, 5)),
                    (dt(2011, 3, 5), dt(2011, 4, 5)),
                    (dt(2011, 4, 5), dt(2011, 4, 28))]
        for i, period in enumerate(ef):
            self.assertEqual(period.start, expected[i][0])
            self.assertEqual(period.end, expected[i][1])

        ef = S3TimePlotEventFrame(dt(2011, 1, 5),
                                  dt(2011, 8, 16),
                                  slots="3 months")
        expected = [(dt(2011, 1, 5), dt(2011, 4, 5)),
                    (dt(2011, 4, 5), dt(2011, 7, 5)),
                    (dt(2011, 7, 5), dt(2011, 8, 16))]
        for i, period in enumerate(ef):
            self.assertEqual(period.start, expected[i][0])
            self.assertEqual(period.end, expected[i][1])

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
        EventTests,
        PeriodTests,
        EventFrameTests,
    )

# END ========================================================================
