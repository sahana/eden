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
    """ Tests for S3TimeSeriesEvent class """

    def testSeries(self):
        """ Test series-method """

        series = S3TimeSeriesEvent.series

        assertEqual = self.assertEqual

        # Explicit None should give {None}
        assertEqual(series(None), set([None]))

        # Single value should give {value}
        assertEqual(series(0), set([0]))
        assertEqual(series("A"), set(["A"]))

        # Empty list should give {None}
        assertEqual(series([]), set())
        assertEqual(series([[], []]), set())

        # List should give equivalent set
        assertEqual(series(["A", "B"]), set(["A", "B"]))
        assertEqual(series(["A", None]), set(["A", None]))
        assertEqual(series(["A", []]), set(["A"]))

        # Nested lists should be flattened
        assertEqual(series(["A", ["B", "C"]]), set(["A", "B", "C"]))
        assertEqual(series(["A", ["B", "A"]]), set(["A", "B"]))

    # -------------------------------------------------------------------------
    def testConstruction(self):
        """ Test event construction """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        start = tp_datetime(2004, 1, 1)
        end = tp_datetime(2004, 3, 21)

        event_id = 1
        values = {"test": 2}

        # Test construction without values
        event = S3TimeSeriesEvent(event_id,
                                  start=start,
                                  end=end,
                                  )

        assertEqual(event.event_id, event_id)
        assertTrue(isinstance(event.values, dict))
        assertEqual(event["test"], None)

        # Test construction with values
        event = S3TimeSeriesEvent(event_id,
                                  start=start,
                                  end=end,
                                  values=values,
                                  )

        assertEqual(event.event_id, event_id)
        assertEqual(event.values, values)
        assertEqual(event["test"], values["test"])

        # Test construction with values and row
        event = S3TimeSeriesEvent(event_id,
                                  start=start,
                                  end=end,
                                  values=values,
                                  row = "A",
                                  )

        self.assertEqual(event.event_id, event_id)
        self.assertEqual(event.values, values)
        self.assertEqual(event["test"], values["test"])
        self.assertEqual(event.rows, set(["A"]))
        self.assertEqual(event.cols, set())

        # Test construction with values and row/col
        event = S3TimeSeriesEvent(event_id,
                                  start=start,
                                  end=end,
                                  values=values,
                                  row = "B",
                                  col = [1, 4, 7],
                                  )

        self.assertEqual(event.event_id, event_id)
        self.assertEqual(event.values, values)
        self.assertEqual(event["test"], values["test"])
        self.assertEqual(event.rows, set(["B"]))
        self.assertEqual(event.cols, set([1, 4, 7]))

    # -------------------------------------------------------------------------
    def testComparison(self):
        """ Test comparison method __lt__ for events (by sorting them) """

        data = [
            (8, (2012,1,12), (2013,9,19)),
            (2, None, (2013,4,21)),
            (6, (2013,4,14), (2013,5,7)),
            (3, (2012,4,21), (2013,6,3)),
            (4, (2013,4,18), (2013,5,27)),
        ]

        events = []
        for event_id, start, end in data:
            event_start = tp_datetime(*start) if start else None
            event_end = tp_datetime(*end) if end else None
            event = S3TimeSeriesEvent(event_id,
                                      start = event_start,
                                      end = event_end,
                                      )
            events.append(event)

        order = [event.event_id for event in sorted(events)]
        self.assertEqual(order, [2, 8, 3, 6, 4])

# =============================================================================
class PeriodTests(unittest.TestCase):
    """ Tests for S3TimeSeriesPeriod """

    def setUp(self):

        # Period
        start = tp_datetime(2013,4,1)
        end = tp_datetime(2013,7,1)

        period = S3TimeSeriesPeriod(start=start, end=end)

        # Add current events
        events = [
            # 7 days
            (1,  (2013,4,1), (2013,4,7),  {"base": 10, "slope": 2}, "A", 1),
            (2,  (2013,4,3), (2013,4,9),  {"base": 20, "slope": 5}, "A", 2),
            (3,  (2013,4,5), (2013,4,11), {"base": 30, "slope": 2}, "B", 2),
            (4,  (2013,4,7), (2013,4,13), {"base": 40, "slope": 5}, "B", 3),
            # 10 days
            (5,  (2013,5,1), (2013,5,10), {"base": 50, "slope": 5}, "C", 1),
            (6,  (2013,5,3), (2013,5,12), {"base": 60, "slope": 2}, "C", 2),
            (7,  (2013,5,5), (2013,5,14), {"base": 70, "slope": 5}, "A", 1),
            (8,  (2013,5,7), (2013,5,16), {"base": 80, "slope": 2}, "A", 2),
            # 20 days
            (9,  (2013,6,1), (2013,6,20), {"base": 100, "slope": 4}, "B", 2),
            (10, (2013,6,3), (2013,6,22), {"base": 200, "slope": 7}, "B", 3),
            (11, (2013,6,5), (2013,6,24), {"base": 300, "slope": 4}, "C", 1),
            (12, (2013,6,12), None, {"base": 400, "slope": 7}, "C", 3),
        ]
        for event_id, start, end, values, row, col in events:
            event_start = tp_datetime(*start) if start else None
            event_end = tp_datetime(*end) if end else None
            event = S3TimeSeriesEvent(event_id,
                                      start = event_start,
                                      end = event_end,
                                      values = values,
                                      row = row,
                                      col = col,
                                      )
            period.add_current(event)
        self.current_events = events

        # Add previous events
        events = [
            # 10 days
            (13,  (2012,8,1), (2012,8,10), {"base": 20, "slope": 5}, "A", 3),
            (14,  (2012,8,3), (2012,8,12), {"base": 20, "slope": 5}, "B", 2),
            (15,  None, (2012,8,14), {"base": 20, "slope": 5}, "C", 1),
            (16,  (2012,8,7), (2012,8,16), {"base": 20, "slope": 5}, "C", 3),
        ]
        for event_id, start, end, values, row, col in events:
            event_start = tp_datetime(*start) if start else None
            event_end = tp_datetime(*end) if end else None
            event = S3TimeSeriesEvent(event_id,
                                      start = event_start,
                                      end = event_end,
                                      values = values,
                                      row = row,
                                      col = col,
                                      )
            period.add_previous(event)
        self.previous_events = events

        # Store period
        self.period = period

    # -------------------------------------------------------------------------
    def testEvents(self):
        """ Verify events in test period """

        assertTrue = self.assertTrue

        cevents = self.period.cevents
        for item in self.current_events:
            assertTrue(item[0] in cevents)

        pevents = self.period.pevents
        for item in self.previous_events:
            assertTrue(item[0] in pevents)

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
            start, end, expected_duration = event
            tp_event = S3TimeSeriesEvent(index,
                                         start=tp_datetime(*start),
                                         end=tp_datetime(*end),
                                         )
            duration = period.duration(tp_event, "days")
            self.assertEqual(duration, expected_duration,
                             msg = "Incorrect result for duration of event %s: %s != %s." %
                                   (index + 1, duration, expected_duration))

    # -------------------------------------------------------------------------
    def testGrouping(self):
        """ Test grouping of period events """

        period = self.period
        period.group()

        assertTrue = self.assertTrue
        assertEqual = self.assertEqual

        # Check rows
        expected_rows = {"A": ((1, 2, 7, 8), ()),
                         "B": ((3, 4, 9, 10), ()),
                         "C": ((5, 6, 11, 12), ()),
                         }
        rows = period._rows
        assertEqual(set(rows.keys()), set(expected_rows.keys()))
        for k, v in rows.items():
            expected_current = set(expected_rows.get(k)[0])
            assertEqual(v[0], expected_current,
                        msg = "Row %s current events: %s != %s" %
                              (k, v[0], expected_current))
            expected_previous = set(expected_rows.get(k)[1])
            assertEqual(v[1], expected_previous,
                        msg = "Row %s previous events: %s != %s" %
                              (k, v[1], expected_previous))

        # Check columns
        expected_cols = {1: ((1, 5, 7, 11), ()),
                         2: ((2, 3, 6, 8, 9), ()),
                         3: ((4, 10, 12), ()),
                         }
        cols = period._cols
        assertEqual(set(cols.keys()), set(expected_cols.keys()))
        for k, v in cols.items():
            expected_current = set(expected_cols.get(k)[0])
            assertEqual(v[0], expected_current,
                        msg = "Row %s current events: %s != %s" %
                              (k, v[0], expected_current))
            expected_previous = set(expected_cols.get(k)[1])
            assertEqual(v[1], expected_previous,
                        msg = "Row %s previous events: %s != %s" %
                              (k, v[1], expected_previous))

        # Check matrix
        expected_matrix = {("A", 1): ((1, 7), ()),
                           ("A", 2): ((2, 8), ()),
                           #("A", 3): (empty),
                           #("B", 1): (empty),
                           ("B", 2): ((3, 9), ()),
                           ("B", 3): ((4, 10), ()),
                           ("C", 1): ((5, 11), ()),
                           ("C", 2): ((6,), ()),
                           ("C", 3): ((12,), ()),
                           }
        matrix = period._matrix
        assertEqual(set(matrix.keys()), set(expected_matrix.keys()))
        for k, v in matrix.items():
            expected_current = set(expected_matrix.get(k)[0])
            assertEqual(v[0], expected_current,
                        msg = "Row %s current events: %s != %s" %
                              (k, v[0], expected_current))
            expected_previous = set(expected_matrix.get(k)[1])
            assertEqual(v[1], expected_previous,
                        msg = "Row %s previous events: %s != %s" %
                              (k, v[1], expected_previous))

    # -------------------------------------------------------------------------
    def testGroupingCumulative(self):
        """ Test grouping of period events including previous events """

        period = self.period
        period.group(cumulative=True)

        assertTrue = self.assertTrue
        assertEqual = self.assertEqual

        # Check rows
        expected_rows = {"A": ((1, 2, 7, 8), (13,)),
                         "B": ((3, 4, 9, 10), (14,)),
                         "C": ((5, 6, 11, 12), (15,16)),
                         }
        rows = period._rows
        assertEqual(set(rows.keys()), set(expected_rows.keys()))
        for k, v in rows.items():
            expected_current = set(expected_rows.get(k)[0])
            assertEqual(v[0], expected_current,
                        msg = "Row %s current events: %s != %s" %
                              (k, v[0], expected_current))
            expected_previous = set(expected_rows.get(k)[1])
            assertEqual(v[1], expected_previous,
                        msg = "Row %s previous events: %s != %s" %
                              (k, v[1], expected_previous))

        # Check columns
        expected_cols = {1: ((1, 5, 7, 11), (15,)),
                         2: ((2, 3, 6, 8, 9), (14,)),
                         3: ((4, 10, 12), (13, 16)),
                         }
        cols = period._cols
        assertEqual(set(cols.keys()), set(expected_cols.keys()))
        for k, v in cols.items():
            expected_current = set(expected_cols.get(k)[0])
            assertEqual(v[0], expected_current,
                        msg = "Row %s current events: %s != %s" %
                              (k, v[0], expected_current))
            expected_previous = set(expected_cols.get(k)[1])
            assertEqual(v[1], expected_previous,
                        msg = "Row %s previous events: %s != %s" %
                              (k, v[1], expected_previous))

        # Check matrix
        expected_matrix = {("A", 1): ((1, 7), ()),
                           ("A", 2): ((2, 8), ()),
                           ("A", 3): ((), (13,)),
                           #("B", 1): (empty),
                           ("B", 2): ((3, 9), (14,)),
                           ("B", 3): ((4, 10), ()),
                           ("C", 1): ((5, 11), (15,)),
                           ("C", 2): ((6,), ()),
                           ("C", 3): ((12,), (16,)),
                           }
        matrix = period._matrix
        assertEqual(set(matrix.keys()), set(expected_matrix.keys()))
        for k, v in matrix.items():
            expected_current = set(expected_matrix.get(k)[0])
            assertEqual(v[0], expected_current,
                        msg = "Row %s current events: %s != %s" %
                              (k, v[0], expected_current))
            expected_previous = set(expected_matrix.get(k)[1])
            assertEqual(v[1], expected_previous,
                        msg = "Row %s previous events: %s != %s" %
                              (k, v[1], expected_previous))

    # -------------------------------------------------------------------------
    def testAggregateCount(self):
        """ Test aggregation: count """

        period = self.period
        assertEqual = self.assertEqual

        # Aggregate
        totals = period.aggregate(S3TimeSeriesFact("count", "base"))

        # Check rows
        expected_rows = {"A": [4],
                         "B": [4],
                         "C": [4],
                         }
        rows = period.rows
        assertEqual(set(rows.keys()), set(expected_rows.keys()))
        for k, v in rows.items():
            assertEqual(v, expected_rows.get(k),
                        msg = "Row %s: %s != %s" %
                              (k, v, expected_rows.get(k)))

        # Check columns
        expected_cols = {1: [4],
                         2: [5],
                         3: [3],
                         }
        cols = period.cols
        assertEqual(set(cols.keys()), set(expected_cols.keys()))
        for k, v in cols.items():
            assertEqual(v, expected_cols.get(k),
                        msg = "Column %s: %s != %s" %
                              (k, v, expected_cols.get(k)))

        # Check matrix
        expected_matrix = {("A", 1): [2],
                           ("A", 2): [2],
                           ("B", 2): [2],
                           ("B", 3): [2],
                           ("C", 1): [2],
                           ("C", 2): [1],
                           ("C", 3): [1],
                           }
        matrix = period.matrix
        assertEqual(set(matrix.keys()), set(expected_matrix.keys()))
        for k, v in matrix.items():
            assertEqual(v, expected_matrix.get(k),
                        msg = "Cell %s: %s != %s" %
                              (k, v, expected_matrix.get(k)))

        # Check total
        expected_totals = [12]
        assertEqual(period.totals, expected_totals)
        assertEqual(totals, expected_totals)

    # -------------------------------------------------------------------------
    def testAggregateSum(self):
        """ Test aggregation: sum """

        period = self.period
        assertEqual = self.assertEqual

        # Aggregate
        totals = period.aggregate(S3TimeSeriesFact("sum", "base"))

        # Check rows
        expected_rows = {"A": [180],
                         "B": [370],
                         "C": [810],
                         }
        rows = period.rows
        assertEqual(set(rows.keys()), set(expected_rows.keys()))
        for k, v in rows.items():
            assertEqual(v, expected_rows.get(k),
                        msg = "Row %s: %s != %s" %
                              (k, v, expected_rows.get(k)))

        # Check columns
        expected_cols = {1: [430],
                         2: [290],
                         3: [640],
                         }
        cols = period.cols
        assertEqual(set(cols.keys()), set(expected_cols.keys()))
        for k, v in cols.items():
            assertEqual(v, expected_cols.get(k),
                        msg = "Column %s: %s != %s" %
                              (k, v, expected_cols.get(k)))

        # Check matrix
        expected_matrix = {("A", 1): [80],
                           ("A", 2): [100],
                           ("B", 2): [130],
                           ("B", 3): [240],
                           ("C", 1): [350],
                           ("C", 2): [60],
                           ("C", 3): [400],
                           }
        matrix = period.matrix
        assertEqual(set(matrix.keys()), set(expected_matrix.keys()))
        for k, v in matrix.items():
            assertEqual(v, expected_matrix.get(k),
                        msg = "Cell %s: %s != %s" %
                              (k, v, expected_matrix.get(k)))

        # Check total
        expected_totals = [1360]
        assertEqual(period.totals, expected_totals)
        assertEqual(totals, expected_totals)

    # -------------------------------------------------------------------------
    def testAggregateAvg(self):
        """ Test aggregation: avg """

        period = self.period
        assertEqual = self.assertEqual
        assertAlmostEqual = self.assertAlmostEqual

        # Aggregate
        totals = period.aggregate(S3TimeSeriesFact("avg", "base"))

        # Check rows
        expected_rows = {"A": [45],
                         "B": [92.5],
                         "C": [202.5],
                         }
        rows = period.rows
        assertEqual(set(rows.keys()), set(expected_rows.keys()))
        for k, v in rows.items():
            expected = expected_rows.get(k)
            for i, expected_value in enumerate(expected):
                assertAlmostEqual(v[i], expected_value,
                                  msg = "Row %s: %s != %s" %
                                        (k, v, expected_rows.get(k)))

        # Check columns
        expected_cols = {1: [107.5],
                         2: [58],
                         3: [213.3333333],
                         }
        cols = period.cols
        assertEqual(set(cols.keys()), set(expected_cols.keys()))
        for k, v in cols.items():
            expected = expected_cols.get(k)
            for i, expected_value in enumerate(expected):
                assertAlmostEqual(v[i], expected_value,
                                  msg = "Column %s: %s != %s" %
                                         (k, v, expected_cols.get(k)))

        # Check matrix
        expected_matrix = {("A", 1): [40],
                           ("A", 2): [50],
                           ("B", 2): [65],
                           ("B", 3): [120],
                           ("C", 1): [175],
                           ("C", 2): [60],
                           ("C", 3): [400],
                           }
        matrix = period.matrix
        assertEqual(set(matrix.keys()), set(expected_matrix.keys()))
        for k, v in matrix.items():
            expected = expected_matrix.get(k)
            for i, expected_value in enumerate(expected):
                assertAlmostEqual(v[i], expected_value,
                                  msg = "Cell %s: %s != %s" %
                                        (k, v, expected_matrix.get(k)))

        # Check total
        expected_totals = [113.3333333]
        assertEqual(len(period.totals), 1)
        assertAlmostEqual(period.totals[0], expected_totals[0])
        assertEqual(len(totals), 1)
        assertAlmostEqual(totals[0], expected_totals[0])

    # -------------------------------------------------------------------------
    def testAggregateMinMax(self):
        """ Test aggregation: min/max (combined) """

        period = self.period
        assertEqual = self.assertEqual

        # Aggregate
        totals = period.aggregate([S3TimeSeriesFact("min", "base"),
                                   S3TimeSeriesFact("max", "base"),
                                   ],
                                  )

        # Check rows
        expected_rows = {"A": [10, 80],
                         "B": [30, 200],
                         "C": [50, 400],
                         }
        rows = period.rows
        assertEqual(set(rows.keys()), set(expected_rows.keys()))
        for k, v in rows.items():
            assertEqual(v, expected_rows.get(k),
                        msg = "Row %s: %s != %s" %
                              (k, v, expected_rows.get(k)))

        # Check columns
        expected_cols = {1: [10, 300],
                         2: [20, 100],
                         3: [40, 400],
                         }
        cols = period.cols
        assertEqual(set(cols.keys()), set(expected_cols.keys()))
        for k, v in cols.items():
            assertEqual(v, expected_cols.get(k),
                        msg = "Column %s: %s != %s" %
                              (k, v, expected_cols.get(k)))

        # Check matrix
        expected_matrix = {("A", 1): [10, 70],
                           ("A", 2): [20, 80],
                           ("B", 2): [30, 100],
                           ("B", 3): [40, 200],
                           ("C", 1): [50, 300],
                           ("C", 2): [60, 60],
                           ("C", 3): [400, 400],
                           }
        matrix = period.matrix
        assertEqual(set(matrix.keys()), set(expected_matrix.keys()))
        for k, v in matrix.items():
            assertEqual(v, expected_matrix.get(k),
                        msg = "Cell %s: %s != %s" %
                              (k, v, expected_matrix.get(k)))

        # Check total
        expected_totals = [10, 400]
        assertEqual(period.totals, expected_totals)
        assertEqual(totals, expected_totals)

    # -------------------------------------------------------------------------
    def testAggregateCumulate(self):
        """ Test aggregation: sum/cumulate (combined) """

        period = self.period
        assertEqual = self.assertEqual

        # Aggregate
        totals = period.aggregate([S3TimeSeriesFact("sum", "base"),
                                   S3TimeSeriesFact("cumulate",
                                                    "base",
                                                    slope="slope",
                                                    interval="days",
                                                    ),
                                   ]
                                  )

        # Check rows
        expected_rows = {"A": [180, 369],
                         "B": [370, 709],
                         "C": [810, 1170],
                         }
        rows = period.rows
        assertEqual(set(rows.keys()), set(expected_rows.keys()))
        for k, v in rows.items():
            assertEqual(v, expected_rows.get(k),
                        msg = "Row %s: %s != %s" %
                              (k, v, expected_rows.get(k)))

        # Check columns
        expected_cols = {1: [430, 624],
                         2: [290, 529],
                         3: [640, 1095],
                         }
        cols = period.cols
        assertEqual(set(cols.keys()), set(expected_cols.keys()))
        for k, v in cols.items():
            assertEqual(v, expected_cols.get(k),
                        msg = "Column %s: %s != %s" %
                              (k, v, expected_cols.get(k)))

        # Check matrix
        expected_matrix = {("A", 1): [80, 144],
                           ("A", 2): [100, 155],
                           ("A", 3): [0, 70],
                           ("B", 2): [130, 294],
                           ("B", 3): [240, 415],
                           ("C", 1): [350, 480],
                           ("C", 2): [60, 80],
                           ("C", 3): [400, 610],
                           }
        matrix = period.matrix
        assertEqual(set(matrix.keys()), set(expected_matrix.keys()))
        for k, v in matrix.items():
            assertEqual(v, expected_matrix.get(k),
                        msg = "Cell %s: %s != %s" %
                              (k, v, expected_matrix.get(k)))

        # Check total
        expected_totals = [1360, 2248]
        assertEqual(period.totals, expected_totals)
        assertEqual(totals, expected_totals)

# =============================================================================
class PeriodTestsSingleAxis(unittest.TestCase):
    """ Tests for S3TimeSeriesPeriod with single pivot axis """

    def setUp(self):

        # Period
        start = tp_datetime(2013,4,1)
        end = tp_datetime(2013,7,1)

        period = S3TimeSeriesPeriod(start=start, end=end)

        # Add current events
        events = [
            # 7 days
            (1,  (2013,4,1), (2013,4,7),  {"base": 10, "slope": 2}, "A"),
            (2,  (2013,4,3), (2013,4,9),  {"base": 20, "slope": 5}, "A"),
            (3,  (2013,4,5), (2013,4,11), {"base": 30, "slope": 2}, "B"),
            (4,  (2013,4,7), (2013,4,13), {"base": 40, "slope": 5}, "B"),
            # 10 days
            (5,  (2013,5,1), (2013,5,10), {"base": 50, "slope": 5}, "C"),
            (6,  (2013,5,3), (2013,5,12), {"base": 60, "slope": 2}, "C"),
            (7,  (2013,5,5), (2013,5,14), {"base": 70, "slope": 5}, "A"),
            (8,  (2013,5,7), (2013,5,16), {"base": 80, "slope": 2}, "A"),
            # 20 days
            (9,  (2013,6,1), (2013,6,20), {"base": 100, "slope": 4}, "B"),
            (10, (2013,6,3), (2013,6,22), {"base": 200, "slope": 7}, "B"),
            (11, (2013,6,5), (2013,6,24), {"base": 300, "slope": 4}, "C"),
            (12, (2013,6,12), None, {"base": 400, "slope": 7}, "C"),
        ]
        for event_id, start, end, values, row in events:
            event_start = tp_datetime(*start) if start else None
            event_end = tp_datetime(*end) if end else None
            event = S3TimeSeriesEvent(event_id,
                                      start = event_start,
                                      end = event_end,
                                      values = values,
                                      row = row,
                                      )
            period.add_current(event)
        self.current_events = events

        # Add previous events
        events = [
            # 10 days
            (13,  (2012,8,1), (2012,8,10), {"base": 20, "slope": 5}, "A"),
            (14,  (2012,8,3), (2012,8,12), {"base": 20, "slope": 5}, "B"),
            (15,  None, (2012,8,14), {"base": 20, "slope": 5}, "C"),
            (16,  (2012,8,7), (2012,8,16), {"base": 20, "slope": 5}, "C"),
        ]
        for event_id, start, end, values, row in events:
            event_start = tp_datetime(*start) if start else None
            event_end = tp_datetime(*end) if end else None
            event = S3TimeSeriesEvent(event_id,
                                      start = event_start,
                                      end = event_end,
                                      values = values,
                                      row = row,
                                      )
            period.add_previous(event)
        self.previous_events = events

        # Store period
        self.period = period

    # -------------------------------------------------------------------------
    def testGrouping(self):
        """ Test grouping of period events (single axis) """

        period = self.period
        period.group()

        assertTrue = self.assertTrue
        assertEqual = self.assertEqual

        # Check rows
        expected_rows = {"A": ((1, 2, 7, 8), ()),
                         "B": ((3, 4, 9, 10), ()),
                         "C": ((5, 6, 11, 12), ()),
                         }
        rows = period._rows
        assertEqual(set(rows.keys()), set(expected_rows.keys()))
        for k, v in rows.items():
            expected_current = set(expected_rows.get(k)[0])
            assertEqual(v[0], expected_current,
                        msg = "Row %s current events: %s != %s" %
                              (k, v[0], expected_current))
            expected_previous = set(expected_rows.get(k)[1])
            assertEqual(v[1], expected_previous,
                        msg = "Row %s previous events: %s != %s" %
                              (k, v[1], expected_previous))

        # Check columns
        assertEqual(period._cols, {})

        # Check matrix
        assertEqual(period._matrix, {})

    # -------------------------------------------------------------------------
    def testGroupingCumulative(self):
        """ Test grouping of period events including previous events (single axis) """

        period = self.period
        period.group(cumulative=True)

        assertTrue = self.assertTrue
        assertEqual = self.assertEqual

        # Check rows
        expected_rows = {"A": ((1, 2, 7, 8), (13,)),
                         "B": ((3, 4, 9, 10), (14,)),
                         "C": ((5, 6, 11, 12), (15, 16)),
                         }
        rows = period._rows
        assertEqual(set(rows.keys()), set(expected_rows.keys()))
        for k, v in rows.items():
            expected_current = set(expected_rows.get(k)[0])
            assertEqual(v[0], expected_current,
                        msg = "Row %s current events: %s != %s" %
                              (k, v[0], expected_current))
            expected_previous = set(expected_rows.get(k)[1])
            assertEqual(v[1], expected_previous,
                        msg = "Row %s previous events: %s != %s" %
                              (k, v[1], expected_previous))

        # Check columns
        assertEqual(period._cols, {})

        # Check matrix
        assertEqual(period._matrix, {})

    # -------------------------------------------------------------------------
    def testAggregateCount(self):
        """ Test aggregation: count (single axis)  """

        period = self.period
        assertEqual = self.assertEqual

        # Aggregate
        totals = period.aggregate(S3TimeSeriesFact("count", "base"))

        # Check rows
        expected_rows = {"A": [4],
                         "B": [4],
                         "C": [4],
                         }
        rows = period.rows
        assertEqual(set(rows.keys()), set(expected_rows.keys()))
        for k, v in rows.items():
            assertEqual(v, expected_rows.get(k),
                        msg = "Row %s: %s != %s" %
                              (k, v, expected_rows.get(k)))

        # Check columns
        assertEqual(period.cols, {})

        # Check matrix
        assertEqual(period.matrix, {})

        # Check total
        expected_totals = [12]
        assertEqual(period.totals, expected_totals)
        assertEqual(totals, expected_totals)

    # -------------------------------------------------------------------------
    def testAggregateSum(self):
        """ Test aggregation: sum (single axis) """

        period = self.period
        assertEqual = self.assertEqual

        # Aggregate
        totals = period.aggregate(S3TimeSeriesFact("sum", "base"))

        # Check rows
        expected_rows = {"A": [180],
                         "B": [370],
                         "C": [810],
                         }
        rows = period.rows
        assertEqual(set(rows.keys()), set(expected_rows.keys()))
        for k, v in rows.items():
            assertEqual(v, expected_rows.get(k),
                        msg = "Row %s: %s != %s" %
                              (k, v, expected_rows.get(k)))

        # Check columns
        assertEqual(period.cols, {})

        # Check matrix
        assertEqual(period.matrix, {})

        # Check total
        expected_totals = [1360]
        assertEqual(period.totals, expected_totals)
        assertEqual(totals, expected_totals)

# =============================================================================
class PeriodTestsNoGroups(unittest.TestCase):
    """ Tests for S3TimeSeriesPeriod without grouping """

    def setUp(self):

        # Period
        start = tp_datetime(2013,4,1)
        end = tp_datetime(2013,7,1)

        period = S3TimeSeriesPeriod(start=start, end=end)

        # Add current events
        events = [
            # 7 days
            (1,  (2013,4,1), (2013,4,7),  {"base": 10, "slope": 2}),
            (2,  (2013,4,3), (2013,4,9),  {"base": 20, "slope": 5}),
            (3,  (2013,4,5), (2013,4,11), {"base": 30, "slope": 2}),
            (4,  (2013,4,7), (2013,4,13), {"base": 40, "slope": 5}),
            # 10 days
            (5,  (2013,5,1), (2013,5,10), {"base": 50, "slope": 5}),
            (6,  (2013,5,3), (2013,5,12), {"base": 60, "slope": 2}),
            (7,  (2013,5,5), (2013,5,14), {"base": 70, "slope": 5}),
            (8,  (2013,5,7), (2013,5,16), {"base": 80, "slope": 2}),
            # 20 days
            (9,  (2013,6,1), (2013,6,20), {"base": 100, "slope": 4}),
            (10, (2013,6,3), (2013,6,22), {"base": 200, "slope": 7}),
            (11, (2013,6,5), (2013,6,24), {"base": 300, "slope": 4}),
            (12, (2013,6,12), None, {"base": 400, "slope": 7}),
        ]
        for event_id, start, end, values in events:
            event_start = tp_datetime(*start) if start else None
            event_end = tp_datetime(*end) if end else None
            event = S3TimeSeriesEvent(event_id,
                                      start = event_start,
                                      end = event_end,
                                      values = values,
                                      )
            period.add_current(event)
        self.current_events = events

        # Add previous events
        events = [
            # 10 days
            (13,  (2012,8,1), (2012,8,10), {"base": 20, "slope": 5}),
            (14,  (2012,8,3), (2012,8,12), {"base": 20, "slope": 5}),
            (15,  None, (2012,8,14), {"base": 20, "slope": 5}),
            (16,  (2012,8,7), (2012,8,16), {"base": 20, "slope": 5}),
        ]
        for event_id, start, end, values in events:
            event_start = tp_datetime(*start) if start else None
            event_end = tp_datetime(*end) if end else None
            event = S3TimeSeriesEvent(event_id,
                                      start = event_start,
                                      end = event_end,
                                      values = values,
                                      )
            period.add_previous(event)
        self.previous_events = events

        # Store period
        self.period = period

    # -------------------------------------------------------------------------
    def testGrouping(self):
        """ Test grouping of period events (no grouping) """

        period = self.period
        period.group()

        assertTrue = self.assertTrue
        assertEqual = self.assertEqual

        # Check rows
        assertEqual(period._rows, {})

        # Check columns
        assertEqual(period._cols, {})

        # Check matrix
        assertEqual(period._matrix, {})

    # -------------------------------------------------------------------------
    def testGroupingCumulative(self):
        """ Test grouping of period events including previous events (no grouping) """

        period = self.period
        period.group(cumulative=True)

        assertTrue = self.assertTrue
        assertEqual = self.assertEqual

        # Check rows
        assertEqual(period._rows, {})

        # Check columns
        assertEqual(period._cols, {})

        # Check matrix
        assertEqual(period._matrix, {})

    # -------------------------------------------------------------------------
    def testAggregateCount(self):
        """ Test aggregation: count (no grouping) """

        period = self.period
        assertEqual = self.assertEqual

        # Aggregate
        totals = period.aggregate(S3TimeSeriesFact("count", "base"))

        # Check rows
        assertEqual(period.rows, {})

        # Check columns
        assertEqual(period.cols, {})

        # Check matrix
        assertEqual(period.matrix, {})

        # Check total
        expected_totals = [12]
        assertEqual(period.totals, expected_totals)
        assertEqual(totals, expected_totals)

    # -------------------------------------------------------------------------
    def testAggregateSum(self):
        """ Test aggregation: sum (no grouping) """

        period = self.period
        assertEqual = self.assertEqual

        # Aggregate
        totals = period.aggregate(S3TimeSeriesFact("sum", "base"))

        # Check rows
        assertEqual(period.rows, {})

        # Check columns
        assertEqual(period.cols, {})

        # Check matrix
        assertEqual(period.matrix, {})

        # Check total
        expected_totals = [1360]
        assertEqual(period.totals, expected_totals)
        assertEqual(totals, expected_totals)

    # -------------------------------------------------------------------------
    def testAggregateCumulate(self):
        """ Test aggregation: cumulate (no grouping) """

        period = self.period
        assertEqual = self.assertEqual

        # Aggregate
        totals = period.aggregate(S3TimeSeriesFact("cumulate",
                                                   "base",
                                                   slope="slope",
                                                   interval="days",
                                                   )
                                  )

        # Check rows
        assertEqual(period.rows, {})

        # Check columns
        assertEqual(period.cols, {})

        # Check matrix
        assertEqual(period.matrix, {})

        # Check total
        expected_totals = [2248]
        assertEqual(period.totals, expected_totals)
        assertEqual(totals, expected_totals)

# =============================================================================
class EventFrameTests(unittest.TestCase):
    """ Tests for S3TimeSeriesEventFrame class """

    def setUp(self):

        data = [
            # Always
            (1, None, None, {"test": 2}),
            # First two quarters
            (2, None, (2012,6,19), {"test": 5}),
            # Last three quarters
            (3, (2012,5,1), None, {"test": 8}),
            # First and Second Quarter
            (4, (2012,1,14), (2012,5,7), {"test": 3}),
            # Second and Third Quarter
            (5, (2012,5,1), (2012,7,21), {"test": 2}),
            # Third and Fourth Quarter
            (6, (2012,8,8), (2012,11,3), {"test": 1}),
            # Only Fourth Quarter
            (7, (2012,10,18), (2013,5,27), {"test": 9}),
            # Ended before Event Frame
            (8, (2011,1,1), (2011,12,6), {"test": 9}),
            # Starting after Event Frame
            (9, (2013,1,18), (2013,5,27), {"test": 3}),
        ]

        events = []
        for event_id, start, end, values in data:
            events.append(S3TimeSeriesEvent(event_id,
                                            start=tp_datetime(*start) if start else None,
                                            end=tp_datetime(*end) if end else None,
                                            values=values,
                                            ))
        self.events = events

    # -------------------------------------------------------------------------
    def testExtend(self):
        """ Test correct grouping of events into periods """

        # Create event frame and add events
        ef = S3TimeSeriesEventFrame(tp_datetime(2012,1,1),
                                    tp_datetime(2012,12,15),
                                    slots="3 months")
        ef.extend(self.events)

        # Expected result (start, end, previous, current, results)
        expected = [
            ((2012, 1, 1), (2012, 4, 1), [8], [1, 2, 4], [10, 5, 117]),
            ((2012, 4, 1), (2012, 7, 1), [8], [1, 2, 3, 4, 5], [20, 8, 150]),
            ((2012, 7, 1), (2012, 10, 1), [8, 2, 4], [1, 3, 5, 6], [13, 8, 176]),
            ((2012, 10, 1), (2012, 12, 15), [8, 2, 4, 5], [1, 3, 6, 7], [20, 9, 211]),
        ]

        # Check
        assertEqual = self.assertEqual
        for i, period in enumerate(ef):
            start, end, previous, current, expected_result = expected[i]

            # Check start/end date of period
            assertEqual(period.start, tp_datetime(*start))
            assertEqual(period.end, tp_datetime(*end))

            # Check current events in period
            event_ids = period.cevents.keys()
            assertEqual(set(event_ids), set(current))

            # Check previous events in period
            event_ids = period.pevents.keys()
            assertEqual(set(event_ids), set(previous))

            # Check aggregation (multi-fact)
            result = period.aggregate([S3TimeSeriesFact("sum", "test"),
                                       S3TimeSeriesFact("max", "test"),
                                       S3TimeSeriesFact("cumulate",
                                                        None,
                                                        slope="test",
                                                        interval="months",
                                                        ),
                                       ])
            assertEqual(result, expected_result)

    # -------------------------------------------------------------------------
    def testPeriodsDays(self):
        """ Test iteration over periods (days) """

        assertEqual = self.assertEqual

        ef = S3TimeSeriesEventFrame(tp_datetime(2011, 1, 5),
                                    tp_datetime(2011, 1, 8),
                                    slots="days")
        expected = [(tp_datetime(2011, 1, 5), tp_datetime(2011, 1, 6)),
                    (tp_datetime(2011, 1, 6), tp_datetime(2011, 1, 7)),
                    (tp_datetime(2011, 1, 7), tp_datetime(2011, 1, 8))]

        for i, period in enumerate(ef):
            assertEqual(period.start, expected[i][0])
            assertEqual(period.end, expected[i][1])

        ef = S3TimeSeriesEventFrame(tp_datetime(2011, 1, 5),
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

        ef = S3TimeSeriesEventFrame(tp_datetime(2011, 1, 5),
                                    tp_datetime(2011, 1, 28),
                                    slots="weeks")
        expected = [(tp_datetime(2011, 1, 5), tp_datetime(2011, 1, 12)),
                    (tp_datetime(2011, 1, 12), tp_datetime(2011, 1, 19)),
                    (tp_datetime(2011, 1, 19), tp_datetime(2011, 1, 26)),
                    (tp_datetime(2011, 1, 26), tp_datetime(2011, 1, 28))]
        for i, period in enumerate(ef):
            assertEqual(period.start, expected[i][0])
            assertEqual(period.end, expected[i][1])

        ef = S3TimeSeriesEventFrame(tp_datetime(2011, 1, 5),
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

        ef = S3TimeSeriesEventFrame(tp_datetime(2011, 1, 5),
                                    tp_datetime(2011, 4, 28),
                                    slots="months")
        expected = [(tp_datetime(2011, 1, 5), tp_datetime(2011, 2, 5)),
                    (tp_datetime(2011, 2, 5), tp_datetime(2011, 3, 5)),
                    (tp_datetime(2011, 3, 5), tp_datetime(2011, 4, 5)),
                    (tp_datetime(2011, 4, 5), tp_datetime(2011, 4, 28))]
        for i, period in enumerate(ef):
            assertEqual(period.start, expected[i][0])
            assertEqual(period.end, expected[i][1])

        ef = S3TimeSeriesEventFrame(tp_datetime(2011, 1, 5),
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

        ts = S3TimeSeries

        result = ts.dtparse("5/2001")
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result, tp_datetime(2001, 5, 1, 0, 0, 0))

        result = ts.dtparse("2007-03")
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result, tp_datetime(2007, 3, 1, 0, 0, 0))

        result = ts.dtparse("1996")
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result, tp_datetime(1996, 1, 1, 0, 0, 0))

        result = ts.dtparse("2008-02-12")
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result, tp_datetime(2008, 2, 12, 0, 0, 0))

        result = ts.dtparse("2008-02-31")
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result, tp_datetime(2008, 3, 2, 0, 0, 0))

        # Empty string defaults to now
        now = datetime.datetime.utcnow()
        result = ts.dtparse("")
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result.year, now.year)
        assertEqual(result.month, now.month)
        assertEqual(result.day, now.day)
        assertEqual(result.hour, now.hour)
        assertEqual(result.minute, now.minute)

        # None defaults to now
        now = datetime.datetime.utcnow()
        result = ts.dtparse(None)
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result.year, now.year)
        assertEqual(result.month, now.month)
        assertEqual(result.day, now.day)
        assertEqual(result.hour, now.hour)
        assertEqual(result.minute, now.minute)

        assertRaises(ValueError, ts.dtparse, "1985-13")
        assertRaises(ValueError, ts.dtparse, "68532")
        assertRaises(ValueError, ts.dtparse, "invalid")

    # -------------------------------------------------------------------------
    def testDtParseRelative(self):
        """ Test dtparse with relative dates """

        assertTrue = self.assertTrue
        assertRaises = self.assertRaises
        assertEqual = self.assertEqual

        ts = S3TimeSeries
        start = datetime.datetime(2014, 1, 3, 11, 30)

        result = ts.dtparse("+1 year", start=start)
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result, datetime.datetime(2015, 1, 3, 11, 30, 0))

        result = ts.dtparse("-3 days", start=start)
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result, datetime.datetime(2013, 12, 31, 11, 30, 0))

        result = ts.dtparse("+5 hours", start=start)
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result, datetime.datetime(2014, 1, 3, 16, 30, 0))

        result = ts.dtparse("-6 months", start=start)
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result, datetime.datetime(2013, 7, 3, 11, 30, 0))

        result = ts.dtparse("+12 weeks", start=start)
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result, datetime.datetime(2014, 3, 28, 11, 30, 0))

        # Empty string defaults to start
        result = ts.dtparse("", start=start)
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result.year, start.year)
        assertEqual(result.month, start.month)
        assertEqual(result.day, start.day)
        assertEqual(result.hour, start.hour)
        assertEqual(result.minute, start.minute)

        # None defaults to start
        result = ts.dtparse(None, start=start)
        assertTrue(isinstance(result, datetime.datetime))
        assertEqual(result.year, start.year)
        assertEqual(result.month, start.month)
        assertEqual(result.day, start.day)
        assertEqual(result.hour, start.hour)
        assertEqual(result.minute, start.minute)

        assertRaises(ValueError, ts.dtparse, "invalid")

# =============================================================================
class TimeSeriesTests(unittest.TestCase):
    """ Tests for S3TimeSeries class """

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

        query = FS("event_type") == "STARTEND"
        resource = s3db.resource("tp_test_events", filter = query)
        ts = S3TimeSeries(resource,
                          event_start = "event_start",
                          event_end = "event_end",
                          )
        ef = ts.event_frame
        # falls back to first start date
        assertEqual(ef.start, tp_datetime(2011, 1, 3, 0, 0, 0))
        assertTrue(is_now(ef.end))

        query = FS("event_type") == "NOSTART"
        resource = s3db.resource("tp_test_events", filter = query)
        ts = S3TimeSeries(resource,
                          event_start = "event_start",
                          event_end = "event_end",
                          )
        ef = ts.event_frame
        # falls back to first end date minus 1 day
        assertEqual(ef.start, tp_datetime(2012, 2, 12, 0, 0, 0))
        assertTrue(is_now(ef.end))

        query = FS("event_type") == "NOEND"
        resource = s3db.resource("tp_test_events", filter = query)
        ts = S3TimeSeries(resource,
                          event_start = "event_start",
                          event_end = "event_end",
                          )
        ef = ts.event_frame
        # falls back to first start date
        assertEqual(ef.start, tp_datetime(2012, 7, 21, 0, 0, 0))
        assertTrue(is_now(ef.end))

        resource = s3db.resource("tp_test_events")
        ts = S3TimeSeries(resource,
                          event_start = "event_start",
                          event_end = "event_end",
                          )
        ef = ts.event_frame
        # falls back to first start date
        assertEqual(ef.start, tp_datetime(2011, 1, 3, 0, 0, 0))
        assertTrue(is_now(ef.end))

    # -------------------------------------------------------------------------
    def testAutomaticSlotLength(self):
        """ Test automatic determination of reasonable aggregation time slot """

        assertEqual = self.assertEqual

        s3db = current.s3db

        query = FS("event_type") == "STARTEND"
        resource = s3db.resource("tp_test_events", filter = query)
        ts = S3TimeSeries(resource,
                          event_start = "event_start",
                          event_end = "event_end",
                          end = "2011-03-01",
                          )
        ef = ts.event_frame
        # falls back to first start date
        assertEqual(ef.start, tp_datetime(2011, 1, 3, 0, 0, 0))
        assertEqual(ef.end, tp_datetime(2011, 3, 1, 0, 0, 0))
        # ~8 weeks => reasonable intervall length: weeks
        assertEqual(ef.slots, "weeks")

        query = FS("event_type") == "NOSTART"
        resource = s3db.resource("tp_test_events", filter = query)
        ts = S3TimeSeries(resource,
                          event_start = "event_start",
                          event_end = "event_end",
                          end = "2013-01-01",
                          )
        ef = ts.event_frame
        # falls back to first end date minus 1 day
        assertEqual(ef.start, tp_datetime(2012, 2, 12, 0, 0, 0))
        assertEqual(ef.end, tp_datetime(2013, 1, 1, 0, 0))
        # ~11 months => reasonable intervall length: months
        assertEqual(ef.slots, "months")

        query = FS("event_type") == "NOEND"
        resource = s3db.resource("tp_test_events", filter = query)
        ts = S3TimeSeries(resource,
                          event_start = "event_start",
                          event_end = "event_end",
                          end = "2016-06-01",
                          )
        ef = ts.event_frame
        # falls back to first start date
        assertEqual(ef.start, tp_datetime(2012, 7, 21, 0, 0, 0))
        assertEqual(ef.end, tp_datetime(2016, 6, 1, 0, 0))
        # ~4 years => reasonable intervall length: 3 months
        assertEqual(ef.slots, "3 months")

        resource = s3db.resource("tp_test_events")
        ts = S3TimeSeries(resource,
                          event_start = "event_start",
                          event_end = "event_end",
                          end = "2011-01-15",
                          )
        ef = ts.event_frame
        # falls back to first start date
        assertEqual(ef.start, tp_datetime(2011, 1, 3, 0, 0, 0))
        assertEqual(ef.end, tp_datetime(2011, 1, 15, 0, 0))
        # ~12 days => reasonable intervall length: days
        assertEqual(ef.slots, "days")

        # Check with manual slot length
        query = FS("event_type") == "NOEND"
        resource = s3db.resource("tp_test_events", filter = query)
        ts = S3TimeSeries(resource,
                          event_start = "event_start",
                          event_end = "event_end",
                          end = "2016-06-01",
                          slots = "years",
                          )
        ef = ts.event_frame
        # falls back to first start date
        assertEqual(ef.start, tp_datetime(2012, 7, 21, 0, 0, 0))
        assertEqual(ef.end, tp_datetime(2016, 6, 1, 0, 0))
        assertEqual(ef.slots, "years")

        # Check with manual start date
        query = FS("event_type") == "STARTEND"
        resource = s3db.resource("tp_test_events", filter = query)
        ts = S3TimeSeries(resource,
                          event_start = "event_start",
                          event_end = "event_end",
                          start = "2011-02-15",
                          end = "2011-03-01",
                          )
        ef = ts.event_frame
        # falls back to first start date
        assertEqual(ef.start, tp_datetime(2011, 2, 15, 0, 0, 0))
        assertEqual(ef.end, tp_datetime(2011, 3, 1, 0, 0, 0))
        # ~14 days => reasonable intervall length: days
        assertEqual(ef.slots, "days")

    # -------------------------------------------------------------------------
    def testEventDataAggregation(self):
        """ Test aggregation of event data """

        s3db = current.s3db

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        PERIODS = "p"
        TIMES = "t"
        VALUE = "v"

        resource = s3db.resource("tp_test_events")
        ts = S3TimeSeries(resource,
                          event_start = "event_start",
                          event_end = "event_end",
                          end = "2013-01-01",
                          slots = "months",
                          facts = [S3TimeSeriesFact("sum", "parameter1")],
                          )

        # Verify correct slot length
        assertEqual(ts.event_frame.slots, "months")

        expected = [
            ((2011,1,3), (2011,2,3), [15]),        # 00 P NS1 NS2 NS3 SE1
            ((2011,2,3), (2011,3,3), [15]),        # 01 P NS1 NS2 NS3 SE1
            ((2011,3,3), (2011,4,3), [15]),        # 02 P NS1 NS2 NS3 SE1
            ((2011,4,3), (2011,5,3), [18]),        # 03 P NS1 NS2 NS3 SE1 SE2
            ((2011,5,3), (2011,6,3), [18]),        # 04 P NS1 NS2 NS3 SE1 SE2
            ((2011,6,3), (2011,7,3), [15]),        # 05 P NS1 NS2 NS3 SE2
            ((2011,7,3), (2011,8,3), [18]),        # 06 P NS1 NS2 NS3 SE2 SE3
            ((2011,8,3), (2011,9,3), [18]),        # 07 P NS1 NS2 NS3 SE2 SE3
            ((2011,9,3), (2011,10,3), [15]),       # 08 P NS1 NS2 NS3 SE3
            ((2011,10,3), (2011,11,3), [15]),      # 09 P NS1 NS2 NS3 SE3
            ((2011,11,3), (2011,12,3), [15]),      # 10 P NS1 NS2 NS3 SE3
            ((2011,12,3), (2012,1,3), [12]),       # 11 P NS1 NS2 NS3
            ((2012,1,3), (2012,2,3), [12]),        # 12 P NS1 NS2 NS3
            ((2012,2,3), (2012,3,3), [12]),        # 13 P NS1 NS2 NS3
            ((2012,3,3), (2012,4,3), [9]),         # 14 P NS2 NS3
            ((2012,4,3), (2012,5,3), [9]),         # 15 P NS2 NS3
            ((2012,5,3), (2012,6,3), [9]),         # 16 P NS2 NS3
            ((2012,6,3), (2012,7,3), [6]),         # 17 P NS3
            ((2012,7,3), (2012,8,3), [9]),         # 18 P NS3 NE1
            ((2012,8,3), (2012,9,3), [9]),         # 19 P NS3 NE1
            ((2012,9,3), (2012,10,3), [6]),        # 20 P NE1
            ((2012,10,3), (2012,11,3), [9]),       # 21 P NE1 NE2
            ((2012,11,3), (2012,12,3), [9]),       # 22 P NE1 NE2
            ((2012,12,3), (2013,1,1), [9]),        # 23 P NE1 NE2
        ]

        result = ts.as_dict()
        periods = result[PERIODS]

        for i, period in enumerate(periods):

            expected_start, expected_end, expected_value = expected[i]
            expected_start = tp_datetime(*expected_start).isoformat()
            expected_end = tp_datetime(*expected_end).isoformat()

            dates = period.get(TIMES)
            assertTrue(isinstance(dates, tuple))

            start, end = dates

            assertEqual(start, expected_start,
                        msg="Period %s start should be %s, but is %s" %
                        (i, expected_start, start))
            assertEqual(end, expected_end,
                        msg="Period %s end should be %s, but is %s" %
                        (i, expected_end, end))

            value = period.get(VALUE)
            assertEqual(value, expected_value,
                        msg="Period %s sum should be %s, but is %s" %
                        (i, expected_value, value))

    # -------------------------------------------------------------------------
    def testEventDataCumulativeAggregation(self):
        """ Test aggregation of event data, cumulative """

        s3db = current.s3db

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        PERIODS = "p"
        TIMES = "t"
        VALUE = "v"

        resource = s3db.resource("tp_test_events")
        ts = S3TimeSeries(resource,
                          event_start = "event_start",
                          event_end = "event_end",
                          start = "2012-01-01",
                          end = "2013-01-01",
                          slots = "months",
                          facts = [S3TimeSeriesFact("cumulate",
                                                    None,
                                                    slope="parameter1",
                                                    interval="months",
                                                    )
                                   ],
                          )

        # Verify correct slot length
        assertEqual(ts.event_frame.slots, "months")

        expected = [
            ((2012,1,1), (2012,2,1), [45]),       # 01 P NS1 NS2 NS3 (SE1 SE2 SE3)
            ((2012,2,1), (2012,3,1), [45]),       # 02 P NS1 NS2 NS3 (SE1 SE2 SE3)
            ((2012,3,1), (2012,4,1), [45]),       # 03 P NS2 NS3 (SE1 SE2 SE3)
            ((2012,4,1), (2012,5,1), [45]),       # 04 P NS2 NS3 (SE1 SE2 SE3)
            ((2012,5,1), (2012,6,1), [45]),       # 05 P NS2 NS3 (SE1 SE2 SE3)
            ((2012,6,1), (2012,7,1), [45]),       # 06 P NS3 (SE1 SE2 SE3)
            ((2012,7,1), (2012,8,1), [48]),       # 07 P NS3 (SE1 SE2 SE3) NE1
            ((2012,8,1), (2012,9,1), [51]),       # 08 P NS3 (SE1 SE2 SE3) NE1
            ((2012,9,1), (2012,10,1), [54]),      # 09 P (SE1 SE2 SE3) NE1
            ((2012,10,1), (2012,11,1), [60]),     # 10 P (SE1 SE2 SE3) NE1 NE2
            ((2012,11,1), (2012,12,1), [66]),     # 11 P (SE1 SE2 SE3) NE1 NE2
            ((2012,12,1), (2013,1,1), [72]),      # 12 P (SE1 SE2 SE3) NE1 NE2
        ]

        result = ts.as_dict()
        periods = result[PERIODS]

        for i, period in enumerate(periods):

            expected_start, expected_end, expected_value = expected[i]
            expected_start = tp_datetime(*expected_start).isoformat()
            expected_end = tp_datetime(*expected_end).isoformat()

            dates = period.get(TIMES)
            assertTrue(isinstance(dates, tuple))

            start, end = dates

            assertEqual(start, expected_start,
                        msg="Period %s start should be %s, but is %s" %
                        (i, expected_start, start))
            assertEqual(end, expected_end,
                        msg="Period %s end should be %s, but is %s" %
                        (i, expected_end, end))

            value = period.get(VALUE)
            assertEqual(value, expected_value,
                        msg="Period %s cumulative sum should be %s, but is %s" %
                        (i, expected_value, value))

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
class FactParserTests(unittest.TestCase):
    """ Tests for S3TimeSeriesFact parser """

    def testFactExpressionParsing(self):
        """ Test parsing of fact expressions """

        parse = S3TimeSeriesFact.parse

        expressions = (
                       # Isolated selector
                       ("id",
                        ((None, "count", "id", None, None),
                         )
                        ),
                       # Normal fact expression
                       ("count(id)",
                        ((None, "count", "id", None, None),
                         )
                        ),
                       # Cumulate with base and slope
                       ("cumulate(value,delta,3weeks)",
                        ((None, "cumulate", "value", "delta", "3weeks"),
                         )
                        ),
                       # Cumulate without base
                       ("cumulate(delta,3weeks)",
                        ((None, "cumulate", None, "delta", "3weeks"),
                         )
                        ),
                       # Cumulate without slope
                       ("cumulate(value)",
                        ((None, "cumulate", "value", None, None),
                         )
                        ),
                       # Normal fact expression, with complex selector
                       ("sum(~.value)",
                        ((None, "sum", "~.value", None, None),
                         )
                        ),
                       # Normal fact expression, with label
                       (("Number of Records", "count(id)"),
                        (("Number of Records", "count", "id", None, None),
                         )
                        ),
                       # List of fact expressions
                       (["count(id)", "sum(value)"],
                        ((None, "count", "id", None, None),
                         (None, "sum", "value", None, None),
                         )
                        ),
                       # List of fact expressions, with label
                       (["count(id)", ("Example", "min(example)")],
                        ((None, "count", "id", None, None),
                         ("Example", "min", "example", None, None),
                         )
                        ),
                       # Multiple fact expressions
                       ("min(other),avg(other)",
                        ((None, "min", "other", None, None),
                         (None, "avg", "other", None, None),
                         )
                        ),
                       # Multiple fact expressions, with label
                       (("Test", "min(other),avg(other)"),
                        (("Test", "min", "other", None, None),
                         ("Test", "avg", "other", None, None),
                         )
                        ),
                       # Mixed list and multi-expression
                       (["count(id)", "sum(value),avg(other)"],
                        ((None, "count", "id", None, None),
                         (None, "sum", "value", None, None),
                         (None, "avg", "other", None, None),
                         )
                        ),
                       # Empty list
                       ([], None),
                       # Invalid method
                       (["count(id)", "invalid(value)"], None),
                       # Missing selector
                       ("count(id),count()", None),
                       )

        assertRaises = self.assertRaises
        assertEqual = self.assertEqual

        i = 0
        for i, (expression, expected) in enumerate(expressions):

            if expected is None:
                with assertRaises(SyntaxError):
                    facts = parse(expression)
            else:
                facts = parse(expression)
                assertEqual(len(facts), len(expected))
                for j, fact in enumerate(facts):
                    label, method, base, slope, interval = expected[j]
                    assertEqual(fact.label, label,
                                msg = "Expression %s/%s - incorrect label: %s != %s" %
                                (i, j, fact.label, label))
                    assertEqual(fact.method, method,
                                msg = "Expression %s/%s - incorrect method: %s != %s" %
                                (i, j, fact.method, method))
                    assertEqual(fact.base, base,
                                msg = "Expression %s/%s - incorrect base: %s != %s" %
                                (i, j, fact.base, base))
                    assertEqual(fact.slope, slope,
                                msg = "Expression %s/%s - incorrect slope: %s != %s" %
                                (i, j, fact.slope, slope))
                    assertEqual(fact.interval, interval,
                                msg = "Expression %s/%s - incorrect interval: %s != %s" %
                                (i, j, fact.interval, interval))

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
        PeriodTestsSingleAxis,
        PeriodTestsNoGroups,
        EventFrameTests,
        DtParseTests,
        TimeSeriesTests,
        FactParserTests,
    )

# END ========================================================================
