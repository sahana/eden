# -*- coding: utf-8 -*-

""" S3 Grouped Items Report Method

    @copyright: 2015 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.

    @status: experimental
"""

__all__ = ("S3GroupedItemsReport",
           )

import math
import sys

from gluon import current

from s3rest import S3Method

# =============================================================================
class S3GroupedItemsReport(S3Method):
    """
        REST Method Handler for Grouped Items Reports

        @todo: page method
        @todo: filter form and ajax method
        @todo: widget method
        @todo: config and URL options, defaults
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Page-render entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        output = {}
        if r.http == "GET":
            r.error(405, current.ERROR.NOT_IMPLEMENTED)
        else:
            r.error(405, current.ERROR.BAD_METHOD)
        return output

    # -------------------------------------------------------------------------
    def widget(self, r, method=None, widget_id=None, visible=True, **attr):
        """
            Summary widget method

            @param r: the S3Request
            @param method: the widget method
            @param widget_id: the widget ID
            @param visible: whether the widget is initially visible
            @param attr: controller attributes
        """

        output = {}
        if r.http == "GET":
            # @todo: add specific methods
            pass
        else:
            r.error(405, current.ERROR.BAD_METHOD)
        return output

# =============================================================================
class S3GroupedItems(object):
    """
        Helper class representing dict-like items grouped by
        attribute values, used by S3GroupedItemsReport
    """

    def __init__(self, items, groupby=None, aggregate=None, values=None):
        """
            Constructor

            @param items: ordered iterable of items (e.g. list, tuple,
                          iterator, Rows), grouping tries to maintain
                          the original item order
            @param groupby: attribute key or ordered iterable of
                            attribute keys (e.g. list, tuple, iterator)
                            for the items to be grouped by; grouping
                            happens in order of appearance of the keys
            @param aggregate: aggregates to compute, list of tuples
                              (method, key)
            @param value: the grouping values for this group (internal)
        """

        self._groups_dict = {}
        self._groups_list = []

        self.values = values or {}

        self._aggregates = {}

        if groupby:
            if isinstance(groupby, basestring):
                # Single grouping key
                groupby = [groupby]
            else:
                groupby = list(groupby)

            self.key = groupby.pop(0)
            self.groupby = groupby
            self.items = None
            for item in items:
                self.add(item)
        else:
            self.key = None
            self.groupby = None
            self.items = list(items)

        if aggregate:
            if type(aggregate) is tuple:
                aggregate = [aggregate]
            for method, key in aggregate:
                self.aggregate(method, key)

    # -------------------------------------------------------------------------
    @property
    def groups(self):
        """ Generator for iteration over subgroups """

        groups = self._groups_dict
        for value in self._groups_list:
            yield groups.get(value)

    # -------------------------------------------------------------------------
    def __getitem__(self, key):
        """
            Getter for the grouping values dict

            @param key: the grouping key

        """

        if type(key) is tuple:
            return self.aggregate(key[0], key[1]).result
        else:
            return self.values.get(key)

    # -------------------------------------------------------------------------
    def add(self, item):
        """
            Add a new item, either to this group or to a subgroup

            @param item: the item
        """

        # Remove all aggregates
        if self._aggregates:
            self._aggregates = {}

        key = self.key
        if key:

            raw = item.get("_row")
            if raw is None:
                value = item.get(key)
            else:
                # Prefer raw values for grouping over representations
                try:
                    value = raw.get(key)
                except AttributeError, TypeError:
                    # _row is not a dict
                    value = item.get(key)

            if type(value) is list:
                # list:type => item belongs into multiple groups
                add_to_group = self.add_to_group
                for v in value:
                    add_to_group(key, v, item)
            else:
                self.add_to_group(key, value, item)
        else:
            # No subgroups
            self.items.append(item)

    # -------------------------------------------------------------------------
    def add_to_group(self, key, value, item):
        """
            Add an item to a subgroup. Create that subgroup if it does not
            yet exist.

            @param key: the grouping key
            @param value: the grouping value for the subgroup
            @param item: the item to add to the subgroup
        """

        groups = self._groups_dict
        if value in groups:
            group = groups[value]
            group.add(item)
        else:
            values = dict(self.values)
            values[key] = value
            group = S3GroupedItems([item],
                                   groupby = self.groupby,
                                   values = values,
                                   )
            groups[value] = group
            self._groups_list.append(value)
        return group

    # -------------------------------------------------------------------------
    def get_values(self, key):
        """
            Get a list of attribute values for the items in this group

            @param key: the attribute key
            @return: the list of values
        """

        if self.items is None:
            return None

        values = []
        append = values.append
        extend = values.extend

        for item in self.items:

            value = item.get(key)
            if type(value) is list:
                extend(value)
            else:
                append(value)
        return values

    # -------------------------------------------------------------------------
    def aggregate(self, method, key):
        """
            Aggregate item attribute values (recursively over subgroups)

            @param method: the aggregation method
            @param key: the attribute key

            @return: an S3GroupAggregate instance
        """

        aggregates = self._aggregates
        if (method, key) in aggregates:
            # Already computed
            return aggregates[(method, key)]

        if self.items is not None:
            # No subgroups => aggregate values in this group
            values = self.get_values(key)
            aggregate = S3GroupAggregate(method, key, values)
        else:
            # Aggregate recursively over subgroups
            combine = S3GroupAggregate.aggregate
            aggregate = combine(group.aggregate(method, key)
                                    for group in self.groups)

        # Store aggregate
        aggregates[(method, key)] = aggregate

        return aggregate

    # -------------------------------------------------------------------------
    def __repr__(self):
        """ Represent this group and all its subgroups as string """

        return self.__represent()

    # -------------------------------------------------------------------------
    def __represent(self, level=0):
        """
            Represent this group and all its subgroups as string

            @param level: the hierarchy level of this group (for indentation)
        """

        output = ""
        indent = " " * level

        key = self.key
        if key:
            for group in self.groups:
                value = group[key]
                if group:
                    group_repr = group.__represent(level = level+1)
                else:
                    group_repr = "[empty group]"
                output = "%s\n%s=> %s: %s\n%s" % \
                         (output, indent, key, value, group_repr)
        else:
            for item in self.items:
                output = "%s\n%s%s" % (output, indent, item)
            output = "%s\n" % output

        return output

# =============================================================================
class S3GroupAggregate(object):
    """ Class representing aggregated values """

    def __init__(self, method, key, values):
        """
            Constructor

            @param method: the aggregation method (count, sum, min, max, avg)
            @param key: the attribute key
            @param values: the attribute values
        """

        self.method = method
        self.key = key

        self.values = values
        self.result = self.__compute(method, values)

    # -------------------------------------------------------------------------
    def __compute(self, method, values):
        """
            Compute the aggregated value

            @param method: the aggregation method
            @param values: the values

            @return: the aggregated value
        """

        if values is None:
            result = None
        else:
            try:
                values = [v for v in values if v is not None]
            except TypeError:
                result = None
            else:
                if method == "count":
                    result = len(set(values))
                elif method == "sum":
                    try:
                        result = math.fsum(values)
                    except (TypeError, ValueError):
                        result = None
                elif method == "min":
                    try:
                        result = min(values)
                    except (TypeError, ValueError):
                        result = None
                elif method == "max":
                    try:
                        result = max(values)
                    except (TypeError, ValueError):
                        result = None
                elif method == "avg":
                    num = len(values)
                    if num:
                        try:
                            result = sum(values) / float(num)
                        except (TypeError, ValueError):
                            result = None
                    else:
                        result = None
                else:
                    result = None
        return result

    # -------------------------------------------------------------------------
    @classmethod
    def aggregate(cls, items):
        """
            Combine sub-aggregates

            @param items: iterable of sub-aggregates

            @return: an S3GroupAggregate instance
        """

        method = None
        key = None
        values = []

        for item in items:

            if method is None:
                method = item.method
                key = item.key

            elif key != item.key or method != item.method:
                raise TypeError

            if item.values:
                values.extend(item.values)

        return cls(method, key, values)

# END =========================================================================
