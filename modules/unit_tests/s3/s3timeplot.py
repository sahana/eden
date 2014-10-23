# -*- coding: utf-8 -*-
#
# Time Plot Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3timeplot.py
#
import datetime
import random
import unittest
import dateutil.tz

from gluon import *
from s3.s3timeplot import *
from s3.s3timeplot import tp_datetime
from s3.s3query import FS

# =============================================================================
class EventTests(unittest.TestCase):

    # -------------------------------------------------------------------------
    def testConstruction(self):
        """ Test event construction """

        start = tp_datetime(2004, 1, 1)
        end = tp_datetime(2004, 3, 21)

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
    """ Tests for S3TimePlotPeriod """

    def setUp(self):

        # Period
        start = tp_datetime(2013,4,1)
        end = tp_datetime(2013,7,1)
        period = S3TimePlotPeriod(start=start, end=end)

        # Add current events
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
                                    start=tp_datetime(*start),
                                    end=tp_datetime(*end),
                                    values=values,
                                    event_type=event_type)
            period.add_current(event)

        # Add previous events
        events = [
            (1, (2012,4,1), (2012,4,21), {"test3": 1.7, "test4": [31]}, "B"),
            (5, (2012,4,14), (2012,5,7), {"test1": 4, "test2": [17, 21]}, "A"),
        ]
        for event_id, start, end, values, event_type in events:
            event = S3TimePlotEvent(event_id,
                                    start=tp_datetime(*start),
                                    end=tp_datetime(*end),
                                    values=values,
                                    event_type=event_type)
            period.add_previous(event)

        # Store period
        self.period = period

    # -------------------------------------------------------------------------
    def testCurrent(self):
        """ Verify current events in period """

        period = self.period
        sets = period.csets

        self.assertTrue("A" in sets)
        self.assertTrue("B" in sets)
        self.assertEqual(len(sets), 2)

        set_A = sets["A"]
        self.assertEqual(len(set_A), 4)
        set_B = sets["B"]
        self.assertEqual(len(set_B), 3)

    # -------------------------------------------------------------------------
    def testPrevious(self):
        """ Verify previous events in period """

        period = self.period
        sets = period.psets

        self.assertTrue("A" in sets)
        self.assertTrue("B" in sets)
        self.assertEqual(len(sets), 2)

        set_A = sets["A"]
        self.assertEqual(len(set_A), 1)
        set_B = sets["B"]
        self.assertEqual(len(set_B), 1)

    # -------------------------------------------------------------------------
    def testDuration(self):
        """ Test computation of event duration before the end of a period """

        events = (
            ((2013, 1, 1, 0, 0, 0), (2013, 1, 31, 0, 0, 0), 31),
            ((2013, 3, 1, 0, 0, 0), (2013, 4, 2, 0, 0, 0), 33),
            ((2013, 3, 8, 0, 0, 0), (2013, 8, 5, 0, 0, 0), 116),
            ((2013, 5, 1, 0, 0, 0), (2013, 9, 21, 0, 0, 0), 62),
            ((2013, 5, 1, 0, 0, 0), (2013, 5, 5, 0, 0, 0), 5),
            ((2013, 8, 5, 0, 0, 0), (2013, 9, 16, 0, 0, 0), 0),
        )
        period = self.period
        
        for index, event in enumerate(events):
            start, end, duration = event
            tp_event = S3TimePlotEvent(index,
                                       start=tp_datetime(*start),
                                       end=tp_datetime(*end),
                                       event_type="TEST")
            d = period._duration(tp_event, "days")
            self.assertEqual(d, duration,
                             msg="Incorrect result for "
                                 "duration of event %s." % (index + 1))
        
    # -------------------------------------------------------------------------
    def testAggregateCount(self):
        """ Test count aggregation method """

        aggregate = self.period.aggregate
        assertEqual = self.assertEqual

        # Test set A
        value = aggregate(method="count", event_type="A")
        assertEqual(value, 4)
        value = aggregate(method="count", event_type="A", fields=["test1"])
        assertEqual(value, 4)
        value = aggregate(method="count", event_type="A", fields=["test2"])
        assertEqual(value, 5)

        # Test set B
        value = aggregate(method="count", event_type="B", fields=["test1"])
        assertEqual(value, 0)
        value = aggregate(method="count", event_type="B", fields=["test3"])
        assertEqual(value, 2)
        value = aggregate(method="count", event_type="B", fields=["test4"])
        assertEqual(value, 3)

        # Test with nonexistent set
        value = aggregate(method="count",
                          event_type="nonexistent", fields=["test1"])
        assertEqual(value, 0)

        # Test without specifying a set
        value = aggregate(method="count", fields=["test1"])
        assertEqual(value, 0)

    # -------------------------------------------------------------------------
    def testAggregateSum(self):
        """ Test sum aggregation method """
        
        aggregate = self.period.aggregate
        assertEqual = self.assertEqual

        # Test set A
        value = aggregate(method="sum", event_type="A")
        assertEqual(value, None)
        value = aggregate(method="sum", event_type="A", fields=["test1"])
        assertEqual(value, 15)
        value = aggregate(method="sum", event_type="A", fields=["test2"])
        assertEqual(value, 76)

        # Test set B
        value = aggregate(method="sum", event_type="B", fields=["test1"])
        assertEqual(value, 0)
        value = aggregate(method="sum", event_type="B", fields=["test3"])
        assertEqual(value, 14.3)
        value = aggregate(method="sum", event_type="B", fields=["test4"])
        assertEqual(value, 159)

        # Test with nonexistent set
        value = aggregate(method="sum",
                          event_type="nonexistent", fields=["test1"])
        assertEqual(value, 0)

        # Test without specifying a set
        value = aggregate(method="sum", fields=["test1"])
        assertEqual(value, 0)

    # -------------------------------------------------------------------------
    def testAggregateAvg(self):
        """ Test avg aggregation method """

        aggregate = self.period.aggregate
        assertEqual = self.assertEqual

        # Test set A
        value = aggregate(method="avg", event_type="A")
        assertEqual(value, None)
        value = aggregate(method="avg", event_type="A", fields=["test1"])
        assertEqual(value, 3.75)
        value = aggregate(method="avg", event_type="A", fields=["test2"])
        assertEqual(value, 15.2)

        # Test set B
        value = aggregate(method="avg", event_type="B", fields=["test1"])
        assertEqual(value, None)
        value = aggregate(method="avg", event_type="B", fields=["test3"])
        assertEqual(value, 7.15)
        value = aggregate(method="avg", event_type="B", fields=["test4"])
        assertEqual(value, 53.0)

        # Test with nonexistent set
        value = aggregate(method="avg",
                          event_type="nonexistent", fields=["test1"])
        assertEqual(value, None)

        # Test without specifying a set
        value = aggregate(method="avg", fields=["test1"])
        assertEqual(value, None)

    # -------------------------------------------------------------------------
    def testAggregateMin(self):
        """ Test min aggregation method """

        aggregate = self.period.aggregate
        assertEqual = self.assertEqual

        # Test set A
        value = aggregate(method="min", event_type="A")
        assertEqual(value, None)
        value = aggregate(method="min", event_type="A", fields=["test1"])
        assertEqual(value, 1)
        value = aggregate(method="min", event_type="A", fields=["test2"])
        assertEqual(value, 11)

        # Test set B
        value = aggregate(method="min", event_type="B", fields=["test1"])
        assertEqual(value, None)
        value = aggregate(method="min", event_type="B", fields=["test3"])
        assertEqual(value, 6.2)
        value = aggregate(method="min", event_type="B", fields=["test4"])
        assertEqual(value, 31)

        # Test with nonexistent set
        value = aggregate(method="min",
                          event_type="nonexistent", fields=["test1"])
        assertEqual(value, None)

        # Test without specifying a set
        value = aggregate(method="min", fields=["test1"])
        assertEqual(value, None)

    # -------------------------------------------------------------------------
    def testAggregateMax(self):
        """ Test max aggregation method """

        aggregate = self.period.aggregate
        assertEqual = self.assertEqual

        # Test set A
        value = aggregate(method="max", event_type="A")
        assertEqual(value, None)
        value = aggregate(method="max", event_type="A", fields=["test1"])
        assertEqual(value, 9)
        value = aggregate(method="max", event_type="A", fields=["test2"])
        assertEqual(value, 21)

        # Test set B
        value = aggregate(method="max", event_type="B", fields=["test1"])
        assertEqual(value, None)
        value = aggregate(method="max", event_type="B", fields=["test3"])
        assertEqual(value, 8.1)
        value = aggregate(method="max", event_type="B", fields=["test4"])
        assertEqual(value, 91)

        # Test with nonexistent set
        value = aggregate(method="max",
                          event_type="nonexistent", fields=["test1"])
        assertEqual(value, None)
        
        # Test without specifying a set
        value = aggregate(method="max", fields=["test1"])
        assertEqual(value, None)
        
    # -------------------------------------------------------------------------
    def testEvents(self):
        """ Test access to events in a period """

        period = self.period
        assertTrue = self.assertTrue
        assertEqual = self.assertEqual

        # Test set A, current events
        events = period.current_events(event_type="A")
        assertTrue(isinstance(events, list))
        assertEqual(len(events), 4)
        event_ids = set([1, 2, 3, 4])
        for event in events:
            assertEqual(event.event_type, "A")
            assertTrue(event.event_id in event_ids)
            event_ids.discard(event.event_id)
        assertEqual(len(event_ids), 0,
                    msg="Current events not present: %s" % event_ids)

        # Test set B, all events
        events = period.events(event_type="B")
        assertTrue(isinstance(events, list))
        assertEqual(len(events), 4)
        event_ids = set([1, 2, 6, 8])
        for event in events:
            assertEqual(event.event_type, "B")
            assertTrue(event.event_id in event_ids)
            event_ids.discard(event.event_id)
        assertEqual(len(event_ids), 0,
                    msg="Events not present: %s" % event_ids)

        # Test set B, previous events
        events = period.previous_events(event_type="B")
        assertTrue(isinstance(events, list))
        assertEqual(len(events), 1)
        event_ids = set([1])
        for event in events:
            assertEqual(event.event_type, "B")
            assertTrue(event.event_id in event_ids)
            event_ids.discard(event.event_id)
        assertEqual(len(event_ids), 0,
                    msg="Previous events not present: %s" % event_ids)

        # Test with nonexistent set
        events = period.events("nonexistent")
        assertEqual(events, [])

        # Test without specifying a set
        events = period.events()
        assertEqual(events, [])

    # -------------------------------------------------------------------------
    def testCount(self):
        """ Test counting of events in a period """
        
        count = self.period.count
        assertEqual = self.assertEqual

        # Test set A
        assertEqual(count("A"), 4)

        # Test set B
        assertEqual(count("B"), 3)

        # Test nonexistent set
        assertEqual(count("nonexistent"), 0)

        # Test without specifying a set
        assertEqual(count(), 0)

# =============================================================================
class EventFrameTests(unittest.TestCase):

    def setUp(self):

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
                                          start=tp_datetime(*start) if start else None,
                                          end=tp_datetime(*end) if end else None,
                                          values=values,
                                          event_type=event_type))
        self.events = events

    # -------------------------------------------------------------------------
    def testExtend(self):
        """ Test correct grouping of events into intervals """

        # Create event frame and add events
        ef = S3TimePlotEventFrame(tp_datetime(2012,1,1),
                                  tp_datetime(2012,12,15),
                                  slots="3 months")
        ef.extend(self.events)

        # Expected result (start, end, previous, current, results)
        expected = [
            ((2012, 1, 1), (2012, 4, 1), [8], [1, 2, 4], (10, 5, 117)),
            ((2012, 4, 1), (2012, 7, 1), [8], [1, 2, 3, 4, 5], (20, 8, 150)),
            ((2012, 7, 1), (2012, 10, 1), [8, 2, 4], [1, 3, 5, 6], (13, 8, 176)),
            ((2012, 10, 1), (2012, 12, 15), [8, 2, 4, 5], [1, 3, 6, 7], (20, 9, 211)),
        ]

        # Check
        assertEqual = self.assertEqual
        for i, period in enumerate(ef):
            start, end, previous, current, expected_result = expected[i]

            # Check start/end date of period
            assertEqual(period.start, tp_datetime(*start))
            assertEqual(period.end, tp_datetime(*end))

            # Check current events in period
            event_ids = [event.event_id for event in period.current_events("A")]
            assertEqual(set(event_ids), set(current))

            # Check previous events in period
            event_ids = [event.event_id for event in period.previous_events("A")]
            assertEqual(set(event_ids), set(previous))

            # Check aggregation
            result = period.aggregate("sum",
                                      fields=["test"],
                                      event_type="A")
            assertEqual(result, expected_result[0])
            
            result = period.aggregate("max",
                                      fields=["test"],
                                      event_type="A")
            assertEqual(result, expected_result[1])
            
            result = period.aggregate("cumulate",
                                      fields=["test"],
                                      arguments=["months"],
                                      event_type="A")
            assertEqual(result, expected_result[2])

    # -------------------------------------------------------------------------
    def testPeriodsDays(self):
        """ Test iteration over periods (days) """

        assertEqual = self.assertEqual
        
        ef = S3TimePlotEventFrame(tp_datetime(2011, 1, 5),
                                  tp_datetime(2011, 1, 8),
                                  slots="days")
        expected = [(tp_datetime(2011, 1, 5), tp_datetime(2011, 1, 6)),
                    (tp_datetime(2011, 1, 6), tp_datetime(2011, 1, 7)),
                    (tp_datetime(2011, 1, 7), tp_datetime(2011, 1, 8))]

        for i, period in enumerate(ef):
            assertEqual(period.start, expected[i][0])
            assertEqual(period.end, expected[i][1])

        ef = S3TimePlotEventFrame(tp_datetime(2011, 1, 5),
                                  tp_datetime(2011, 1, 16),
                                  slots="4 days")
        expected = [(tp_datetime(2011, 1, 5), tp_datetime(2011, 1, 9)),
                    (tp_datetime(2011, 1, 9), tp_datetime(2011, 1, 13)),
                    (tp_datetime(2011, 1, 13), tp_datetime(2011, 1, 16))]
        for i, period in enumerate(ef):
            assertEqual(period.start, expected[i][0])
            assertEqual(period.end, expected[i][1])

    # -------------------------------------------------------------------------
    def testPeriodsWeeks(self):
        """ Test iteration over periods (weeks) """

        assertEqual = self.assertEqual

        ef = S3TimePlotEventFrame(tp_datetime(2011, 1, 5),
                                  tp_datetime(2011, 1, 28),
                                  slots="weeks")
        expected = [(tp_datetime(2011, 1, 5), tp_datetime(2011, 1, 12)),
                    (tp_datetime(2011, 1, 12), tp_datetime(2011, 1, 19)),
                    (tp_datetime(2011, 1, 19), tp_datetime(2011, 1, 26)),
                    (tp_datetime(2011, 1, 26), tp_datetime(2011, 1, 28))]
        for i, period in enumerate(ef):
            assertEqual(period.start, expected[i][0])
            assertEqual(period.end, expected[i][1])

        ef = S3TimePlotEventFrame(tp_datetime(2011, 1, 5),
                                  tp_datetime(2011, 2, 16),
                                  slots="2 weeks")
        expected = [(tp_datetime(2011, 1, 5), tp_datetime(2011, 1, 19)),
                    (tp_datetime(2011, 1, 19), tp_datetime(2011, 2, 2)),
                    (tp_datetime(2011, 2, 2), tp_datetime(2011, 2, 16))]
        for i, period in enumerate(ef):
            assertEqual(period.start, expected[i][0])
            assertEqual(period.end, expected[i][1])
            
    # -------------------------------------------------------------------------
    def testPeriodsMonths(self):
        """ Test iteration over periods (months) """

        assertEqual = self.assertEqual

        ef = S3TimePlotEventFrame(tp_datetime(2011, 1, 5),
                                  tp_datetime(2011, 4, 28),
                                  slots="months")
        expected = [(tp_datetime(2011, 1, 5), tp_datetime(2011, 2, 5)),
                    (tp_datetime(2011, 2, 5), tp_datetime(2011, 3, 5)),
                    (tp_datetime(2011, 3, 5), tp_datetime(2011, 4, 5)),
                    (tp_datetime(2011, 4, 5), tp_datetime(2011, 4, 28))]
        for i, period in enumerate(ef):
            assertEqual(period.start, expected[i][0])
            assertEqual(period.end, expected[i][1])

        ef = S3TimePlotEventFrame(tp_datetime(2011, 1, 5),
                                  tp_datetime(2011, 8, 16),
                                  slots="3 months")
        expected = [(tp_datetime(2011, 1, 5), tp_datetime(2011, 4, 5)),
                    (tp_datetime(2011, 4, 5), tp_datetime(2011, 7, 5)),
                    (tp_datetime(2011, 7, 5), tp_datetime(2011, 8, 16))]
        for i, period in enumerate(ef):
            assertEqual(period.start, expected[i][0])
            assertEqual(period.end, expected[i][1])

# =============================================================================
class DtParseTests(unittest.TestCase):
    """ Test Parsing of Datetime Options """

    # -------------------------------------------------------------------------
    def testDtParseAbsolute(self):
        """ Test dtparse with absolute dates """

        assertTrue = self.assertTrue
        assertRaises = self.assertRaises
        assertEqual = self.assertEqual

        tp = S3TimePlot()

        result = tp.dtparse("5/2001")
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result, tp_datetime(2001, 5, 1, 0, 0, 0))
        
        result = tp.dtparse("2007-03")
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result, tp_datetime(2007, 3, 1, 0, 0, 0))
        
        result = tp.dtparse("1996")
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result, tp_datetime(1996, 1, 1, 0, 0, 0))
        
        result = tp.dtparse("2008-02-12")
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result, tp_datetime(2008, 2, 12, 0, 0, 0))
        
        result = tp.dtparse("2008-02-31")
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result, tp_datetime(2008, 3, 2, 0, 0, 0))

        # Empty string defaults to now
        now = datetime.datetime.utcnow()
        result = tp.dtparse("")
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result.year, now.year)
        assertEqual(result.month, now.month)
        assertEqual(result.day, now.day)
        assertEqual(result.hour, now.hour)
        assertEqual(result.minute, now.minute)

        # None defaults to now
        now = datetime.datetime.utcnow()
        result = tp.dtparse(None)
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result.year, now.year)
        assertEqual(result.month, now.month)
        assertEqual(result.day, now.day)
        assertEqual(result.hour, now.hour)
        assertEqual(result.minute, now.minute)

        assertRaises(ValueError, tp.dtparse, "1985-13")
        assertRaises(ValueError, tp.dtparse, "68532")
        assertRaises(ValueError, tp.dtparse, "invalid")
        
    # -------------------------------------------------------------------------
    def testDtParseRelative(self):
        """ Test dtparse with relative dates """

        assertTrue = self.assertTrue
        assertRaises = self.assertRaises
        assertEqual = self.assertEqual

        tp = S3TimePlot()
        start = datetime.datetime(2014, 1, 3, 11, 30)

        result = tp.dtparse("+1 year", start=start)
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result, datetime.datetime(2015, 1, 3, 11, 30, 0))
        
        result = tp.dtparse("-3 days", start=start)
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result, datetime.datetime(2013, 12, 31, 11, 30, 0))
        
        result = tp.dtparse("+5 hours", start=start)
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result, datetime.datetime(2014, 1, 3, 16, 30, 0))
        
        result = tp.dtparse("-6 months", start=start)
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result, datetime.datetime(2013, 7, 3, 11, 30, 0))
        
        result = tp.dtparse("+12 weeks", start=start)
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result, datetime.datetime(2014, 3, 28, 11, 30, 0))
        
        # Empty string defaults to start
        result = tp.dtparse("", start=start)
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result.year, start.year)
        assertEqual(result.month, start.month)
        assertEqual(result.day, start.day)
        assertEqual(result.hour, start.hour)
        assertEqual(result.minute, start.minute)

        # None defaults to start
        result = tp.dtparse(None, start=start)
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result.year, start.year)
        assertEqual(result.month, start.month)
        assertEqual(result.day, start.day)
        assertEqual(result.hour, start.hour)
        assertEqual(result.minute, start.minute)

        assertRaises(ValueError, tp.dtparse, "invalid")

# =============================================================================
class TimePlotTests(unittest.TestCase):
    """ Test S3TimePlot Methods """

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        db = current.db
        db.define_table("tp_test_events",
                        Field("event_start", "datetime"),
                        Field("event_end", "datetime"),
                        Field("parameter1", "integer"),
                        Field("parameter2", "double"),
                        Field("event_type"),
                        )
        event_table = db["tp_test_events"]

        events = (("STARTEND",
                   (2011, 1, 3, 0, 0, 0),
                   (2011, 5, 4, 0, 0, 0),
                   ),
                  ("STARTEND",
                   (2011, 4, 6, 0, 0, 0),
                   (2011, 8, 7, 0, 0, 0),
                   ),
                  ("STARTEND",
                   (2011, 7, 9, 0, 0, 0),
                   (2011, 11, 10, 0, 0, 0),
                   ),
                  ("NOSTART",
                   None,
                   (2012, 2, 13, 0, 0, 0),
                   ),
                  ("NOSTART",
                   None,
                   (2012, 5, 16, 0, 0, 0),
                   ),
                  ("NOSTART",
                   None,
                   (2012, 8, 19, 0, 0, 0),
                   ),
                  ("NOEND",
                   (2012, 7, 21, 0, 0, 0),
                   None,
                   ),
                  ("NOEND",
                   (2012, 10, 24, 0, 0, 0),
                   None,
                   ),
                  ("NOEND",
                   (2013, 1, 27, 0, 0, 0),
                   None,
                   ),
                  ("PERMANENT",
                   None,
                   None,
                   ),
        )
        
        for event_type, start, end in events:
            event_start = tp_datetime(*start) if start else None
            event_end = tp_datetime(*end) if end else None
            record = {
                "event_type": event_type,
                "event_start": event_start,
                "event_end": event_end,
                "parameter1": 3,
                "parameter2": 0.5,
            }
            event_table.insert(**record)

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        db = current.db
        db.tp_test_events.drop()

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True
        
    # -------------------------------------------------------------------------
    def tearDown(self):

        current.auth.override = False

    # -------------------------------------------------------------------------
    def testAutomaticInterval(self):
        """ Test automatic determination of interval start and end """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue
        is_now = self.is_now

        s3db = current.s3db
        resource = s3db.resource("tp_test_events")
        
        event_start = resource.resolve_selector("event_start")
        event_end =  resource.resolve_selector("event_end")

        tp = S3TimePlot()

        query = FS("event_type") == "STARTEND"
        tp.resource = s3db.resource("tp_test_events", filter = query)
        ef = tp.create_event_frame(tp.resource, event_start, event_end)
        # falls back to first start date
        assertEqual(ef.start, tp_datetime(2011, 1, 3, 0, 0, 0))
        assertTrue(is_now(ef.end))

        query = FS("event_type") == "NOSTART"
        tp.resource = s3db.resource("tp_test_events", filter = query)
        ef = tp.create_event_frame(tp.resource, event_start, event_end)
        # falls back to first end date minus 1 day
        assertEqual(ef.start, tp_datetime(2012, 2, 12, 0, 0, 0))
        assertTrue(is_now(ef.end))

        query = FS("event_type") == "NOEND"
        tp.resource = s3db.resource("tp_test_events", filter = query)
        ef = tp.create_event_frame(tp.resource, event_start, event_end)
        # falls back to first start date
        assertEqual(ef.start, tp_datetime(2012, 7, 21, 0, 0, 0))
        assertTrue(is_now(ef.end))

        tp.resource = s3db.resource("tp_test_events")
        ef = tp.create_event_frame(tp.resource, event_start, event_end)
        # falls back to first start date
        assertEqual(ef.start, tp_datetime(2011, 1, 3, 0, 0, 0))
        assertTrue(is_now(ef.end))

    # -------------------------------------------------------------------------
    def testAutomaticSlotLength(self):
        """ Test automatic determination of reasonable aggregation time slot """

        assertEqual = self.assertEqual
        
        s3db = current.s3db
        resource = s3db.resource("tp_test_events")

        event_start = resource.resolve_selector("event_start")
        event_end =  resource.resolve_selector("event_end")

        tp = S3TimePlot()

        end = "2011-03-01"
        query = FS("event_type") == "STARTEND"
        tp.resource = s3db.resource("tp_test_events", filter = query)
        ef = tp.create_event_frame(tp.resource, event_start, event_end, end=end)
        # falls back to first start date
        assertEqual(ef.start, tp_datetime(2011, 1, 3, 0, 0, 0))
        assertEqual(ef.end, tp_datetime(2011, 3, 1, 0, 0, 0))
        # ~8 weeks => reasonable intervall length: weeks
        assertEqual(ef.slots, "weeks")

        end = "2013-01-01"
        query = FS("event_type") == "NOSTART"
        tp.resource = s3db.resource("tp_test_events", filter = query)
        ef = tp.create_event_frame(tp.resource, event_start, event_end, end=end)
        # falls back to first end date minus 1 day
        assertEqual(ef.start, tp_datetime(2012, 2, 12, 0, 0, 0))
        assertEqual(ef.end, tp_datetime(2013, 1, 1, 0, 0))
        # ~11 months => reasonable intervall length: months
        assertEqual(ef.slots, "months")

        end = "2016-06-01"
        query = FS("event_type") == "NOEND"
        tp.resource = s3db.resource("tp_test_events", filter = query)
        ef = tp.create_event_frame(tp.resource, event_start, event_end, end=end)
        # falls back to first start date
        assertEqual(ef.start, tp_datetime(2012, 7, 21, 0, 0, 0))
        assertEqual(ef.end, tp_datetime(2016, 6, 1, 0, 0))
        # ~4 years => reasonable intervall length: 3 months
        assertEqual(ef.slots, "3 months")

        end = "2011-01-15"
        tp.resource = s3db.resource("tp_test_events")
        ef = tp.create_event_frame(tp.resource, event_start, event_end, end=end)
        # falls back to first start date
        assertEqual(ef.start, tp_datetime(2011, 1, 3, 0, 0, 0))
        assertEqual(ef.end, tp_datetime(2011, 1, 15, 0, 0))
        # ~12 days => reasonable intervall length: days
        assertEqual(ef.slots, "days")

        # Check with manual slot length
        end = "2016-06-01"
        query = FS("event_type") == "NOEND"
        tp.resource = s3db.resource("tp_test_events", filter = query)
        ef = tp.create_event_frame(tp.resource, event_start, event_end, end=end, slots="years")
        # falls back to first start date
        assertEqual(ef.start, tp_datetime(2012, 7, 21, 0, 0, 0))
        assertEqual(ef.end, tp_datetime(2016, 6, 1, 0, 0))
        assertEqual(ef.slots, "years")

        # Check with manual start date
        start = "2011-02-15"
        end = "2011-03-01"
        query = FS("event_type") == "STARTEND"
        tp.resource = s3db.resource("tp_test_events", filter = query)
        ef = tp.create_event_frame(tp.resource, event_start, event_end, start=start, end=end)
        # falls back to first start date
        assertEqual(ef.start, tp_datetime(2011, 2, 15, 0, 0, 0))
        assertEqual(ef.end, tp_datetime(2011, 3, 1, 0, 0, 0))
        # ~14 days => reasonable intervall length: days
        assertEqual(ef.slots, "days")

    # -------------------------------------------------------------------------
    def testEventDataAggregation(self):
        """ Test aggregation of event data """
        
        s3db = current.s3db
        resource = s3db.resource("tp_test_events")

        tp = S3TimePlot()
        tp.resource = resource
        
        event_start = resource.resolve_selector("event_start")
        event_end =  resource.resolve_selector("event_end")
        fact1 = resource.resolve_selector("parameter1")
        fact2 = resource.resolve_selector("parameter2")
        
        end = "2013-01-01"
        ef = tp.create_event_frame(tp.resource, 
                                   event_start,
                                   event_end,
                                   end=end,
                                   slots="months")
        tp.add_event_data(ef, resource, event_start, event_end, [fact1, fact2])

        expected = [
            ((2011,1,3), (2011,2,3), 15),        # 00 P NS1 NS2 NS3 SE1
            ((2011,2,3), (2011,3,3), 15),        # 01 P NS1 NS2 NS3 SE1
            ((2011,3,3), (2011,4,3), 15),        # 02 P NS1 NS2 NS3 SE1
            ((2011,4,3), (2011,5,3), 18),        # 03 P NS1 NS2 NS3 SE1 SE2
            ((2011,5,3), (2011,6,3), 18),        # 04 P NS1 NS2 NS3 SE1 SE2
            ((2011,6,3), (2011,7,3), 15),        # 05 P NS1 NS2 NS3 SE2
            ((2011,7,3), (2011,8,3), 18),        # 06 P NS1 NS2 NS3 SE2 SE3
            ((2011,8,3), (2011,9,3), 18),        # 07 P NS1 NS2 NS3 SE2 SE3
            ((2011,9,3), (2011,10,3), 15),       # 08 P NS1 NS2 NS3 SE3
            ((2011,10,3), (2011,11,3), 15),      # 09 P NS1 NS2 NS3 SE3
            ((2011,11,3), (2011,12,3), 15),      # 10 P NS1 NS2 NS3 SE3
            ((2011,12,3), (2012,1,3), 12),       # 11 P NS1 NS2 NS3
            ((2012,1,3), (2012,2,3), 12),        # 12 P NS1 NS2 NS3
            ((2012,2,3), (2012,3,3), 12),        # 13 P NS1 NS2 NS3
            ((2012,3,3), (2012,4,3), 9),         # 14 P NS2 NS3
            ((2012,4,3), (2012,5,3), 9),         # 15 P NS2 NS3
            ((2012,5,3), (2012,6,3), 9),         # 16 P NS2 NS3
            ((2012,6,3), (2012,7,3), 6),         # 17 P NS3
            ((2012,7,3), (2012,8,3), 9),         # 18 P NS3 NE1
            ((2012,8,3), (2012,9,3), 9),         # 19 P NS3 NE1
            ((2012,9,3), (2012,10,3), 6),        # 20 P NE1
            ((2012,10,3), (2012,11,3), 9),       # 21 P NE1 NE2
            ((2012,11,3), (2012,12,3), 9),       # 22 P NE1 NE2
            ((2012,12,3), (2013,1,1), 9),        # 23 P NE1 NE2
        ]
        
        assertEqual = self.assertEqual

        assertEqual(ef.slots, "months")
        for i, period in enumerate(ef):
            expected_start, expected_end, expected_value = expected[i]
            expected_start = tp_datetime(*expected_start)
            expected_end = tp_datetime(*expected_end)

            assertEqual(period.start, expected_start,
                        msg="Period %s start should be %s, but is %s" %
                        (i, expected_start, period.start))
            assertEqual(period.end, expected_end,
                        msg="Period %s end should be %s, but is %s" %
                        (i, expected_end, period.end))
            value1 = period.aggregate(method="sum",
                                      fields=[fact1.colname],
                                      event_type=resource.tablename)
            assertEqual(value1, expected_value,
                        msg="Period %s sum should be %s, but is %s" %
                        (i, expected_value, value1))

            # Indirect count-check: average should be constant
            value2 = period.aggregate(method="avg",
                                      fields=[fact2.colname],
                                      event_type=resource.tablename)
            assertEqual(value2, 0.5)

    # -------------------------------------------------------------------------
    def testEventDataCumulativeAggregation(self):
        """ Test aggregation of event data, cumulative """

        s3db = current.s3db
        resource = s3db.resource("tp_test_events")

        tp = S3TimePlot()
        tp.resource = resource

        event_start = resource.resolve_selector("event_start")
        event_end =  resource.resolve_selector("event_end")
        fact1 = resource.resolve_selector("parameter1")
        fact2 = resource.resolve_selector("parameter2")

        start = "2012-01-01"
        end = "2013-01-01"
        ef = tp.create_event_frame(tp.resource,
                                   event_start,
                                   event_end,
                                   start=start,
                                   end=end,
                                   slots="months")
        tp.add_event_data(ef,
                          resource,
                          event_start,
                          event_end,
                          [fact1, fact2],
                          cumulative=True,
                          )

        expected = [
            ((2012,1,1), (2012,2,1), 45, 12),       # 01 P NS1 NS2 NS3 (SE1 SE2 SE3)
            ((2012,2,1), (2012,3,1), 45, 12),       # 02 P NS1 NS2 NS3 (SE1 SE2 SE3)
            ((2012,3,1), (2012,4,1), 45, 9),        # 03 P NS2 NS3 (SE1 SE2 SE3)
            ((2012,4,1), (2012,5,1), 45, 9),        # 04 P NS2 NS3 (SE1 SE2 SE3)
            ((2012,5,1), (2012,6,1), 45, 9),        # 05 P NS2 NS3 (SE1 SE2 SE3)
            ((2012,6,1), (2012,7,1), 45, 6),        # 06 P NS3 (SE1 SE2 SE3)
            ((2012,7,1), (2012,8,1), 48, 9),        # 07 P NS3 (SE1 SE2 SE3) NE1
            ((2012,8,1), (2012,9,1), 51, 9),        # 08 P NS3 (SE1 SE2 SE3) NE1
            ((2012,9,1), (2012,10,1), 54, 6),       # 09 P (SE1 SE2 SE3) NE1
            ((2012,10,1), (2012,11,1), 60, 9),      # 10 P (SE1 SE2 SE3) NE1 NE2
            ((2012,11,1), (2012,12,1), 66, 9),      # 11 P (SE1 SE2 SE3) NE1 NE2
            ((2012,12,1), (2013,1,1), 72, 9),       # 12 P (SE1 SE2 SE3) NE1 NE2
        ]

        assertEqual = self.assertEqual

        assertEqual(ef.slots, "months")
        for i, period in enumerate(ef):
            expected_start, expected_end, expected_cumulative, expected_sum = expected[i]
            expected_start = tp_datetime(*expected_start)
            expected_end = tp_datetime(*expected_end)

            # Verify period start and end
            assertEqual(period.start, expected_start,
                        msg="Period %s start should be %s, but is %s" %
                        (i, expected_start, period.start))
            assertEqual(period.end, expected_end,
                        msg="Period %s end should be %s, but is %s" %
                        (i, expected_end, period.end))

            # Verify cumulative value
            value1 = period.aggregate(method="cumulate",
                                      fields=[fact1.colname],
                                      arguments=["months"],
                                      event_type=resource.tablename)
            assertEqual(value1, expected_cumulative,
                        msg="Period %s cumulative sum should be %s, but is %s" %
                        (i, expected_cumulative, value1))

            value1 = period.aggregate(method="sum",
                                      fields=[fact1.colname],
                                      event_type=resource.tablename)
            assertEqual(value1, expected_sum,
                        msg="Period %s sum should be %s, but is %s" %
                        (i, expected_sum, value1))
                        
            # Indirect count-check: average should be constant
            value2 = period.aggregate(method="avg",
                                      fields=[fact2.colname],
                                      event_type=resource.tablename)
            assertEqual(value2, 0.5)

    # -------------------------------------------------------------------------
    @staticmethod
    def is_now(dt):

        now = datetime.datetime.utcnow()
        if dt.year == now.year and \
           dt.month == now.month and \
           dt.day == now.day and \
           dt.hour == now.hour and \
           abs(dt.minute - now.minute) < 5:
            return True
        else:
            return False

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
        DtParseTests,
        TimePlotTests,
    )

# END ========================================================================
