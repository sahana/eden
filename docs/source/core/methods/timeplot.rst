S3 Timeplot
===========

Aggregation and visualisation of one or more numeric facts over a time
axis (endpoint: */timeplot*).

.. figure:: timeplot.png

\

Configuration
-------------

The ``timeplot_options`` table setting is used to configure the report:

.. code-block:: python
   :caption: Example of timeplot_options configuration

    facts = [(T("Number of Tests"), "sum(tests_total)"),
             (T("Number of Positive Test Results"), "sum(tests_positive)"),
             (T("Number of Reports"), "count(id)"),
             ]

    timeframes = [("All up to now", "", "", ""),
                  ("Last 6 Months", "-6months", "", "weeks"),
                  ("Last 3 Months", "-3months", "", "weeks"),
                  ("Last Month", "-1month", "", "days"),
                  ("Last Week", "-1week", "", "days"),
                  ]

    timeplot_options = {
        "fact": facts,
        "timestamp": [(T("per interval"), "date,date"),
                      (T("cumulative"), "date"),
                      ],
        "time": timeframes,
        "defaults": {"fact": facts[:2],
                     "timestamp": "date,date",
                     "time": timeframes[-1],
                     },
        }

    s3db.configure("disease_testing_report",
                   timeplot_options = timeplot_options,
                   )

The attributes of the ``timeplot_options`` setting are as follows:

+-----------+------+-----------------------------------------------------------------+
|Option     |Type  |Explanation                                                      |
+===========+======+=================================================================+
|fact       |list  |The selectable facts as tuples (label, expression)               |
+-----------+------+-----------------------------------------------------------------+
|timestamp  |list  | | Selectable time stamps as tuples *(label, expr)*              |
|           |      | |                                                               |
|           |      | | If *expr* contains two comma-separated field selectors, it is |
|           |      | | interpreted as "start,end".                                   |
|           |      | |                                                               |
|           |      | | If *expr* is a single field selector, it is interpreted as    |
|           |      | | start date; in this case events are treated as open-ended,    |
|           |      | | and hence facts cumulating over time.                         |
+-----------+------+-----------------------------------------------------------------+
|time       |list  | | List of time frames as tuples *(label, start, end, slots)*    |
|           |      | |                                                               |
|           |      | | *start* and *end* can be either absolute dates (ISO-format),  |
|           |      | | or :ref:`relative date expressions <rdt>`, or ``""``.         |
|           |      | |                                                               |
|           |      | | A relative *start* is relative to now.                        |
|           |      | |                                                               |
|           |      | | A relative *end* is relative to *start*, or, if no *start*    |
|           |      | | is specified, it is relative to now.                          |
|           |      | |                                                               |
|           |      | | *start* ``""`` means the date of the earliest recorded        |
|           |      | | event, *end* ``""`` means now.                                |
|           |      | |                                                               |
|           |      | | The *slots* length is the default for the time frame, but can |
|           |      | | be overridden with an explicit slot-selector (see below).     |
+-----------+------+-----------------------------------------------------------------+
|slots      |list  | | List of tuples *(label, expr)*                                |
|           |      | |                                                               |
|           |      | | A separate selector for the slot length is rendered only if   |
|           |      | | this option is configured.                                    |
|           |      | |                                                               |
|           |      | | Otherwise, the slot length is fixed to that specified by the  |
|           |      | | selected time frame option.                                   |
+-----------+------+-----------------------------------------------------------------+
|defaults   |dict  | | Default values for the timeplot options                       |
|           |      | |                                                               |
|           |      | | Same attributes as the top-level attributes, each taking a    |
|           |      | | single item of the respective list (except *fact*, which      |
|           |      | | accepts a list).                                              |
+-----------+------+-----------------------------------------------------------------+

.. _rdt:

Relative Time Expressions
-------------------------

The *start* and *end* parameters for the time frame of the report support relative
expressions of the form ``[<|>][+|-]{n}[year|month|week|day|hour]s``.

The *n* is an integer, e.g.:

.. code-block:: python

   "-1 year"    # one year back
   "+2 weeks"   # two weeks onward

Additionally, the ``<`` and ``>`` markers can be added to indicate the start/end of
the respective calendar period, e.g.:

.. code-block:: python

   "<-1 year"   # one year back, 1st of January
   ">+2 weeks"  # two weeks onward, Sunday

In this context, weeks go from Monday (first day) to Sunday (last day).

.. note::

   Even when using ``<`` and ``>`` markers, the rule that *end* is relative
   to *start* still applies.

   This can be confusing when using these markers for both interval ends, e.g.
   the time frame for January 1st to December 31st of last year is **not**:

      ``("<-1 year", ">-1 year")``

   but actually:

      ``("<-1 year", ">+0 years")``

   ...namely, from the beginning of last year to the end of that **same** year.

   More intuitive in this case is to specify: ``("<-1 year", "+1 year")``.
