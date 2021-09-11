# -*- coding: utf-8 -*-

import re
counted_dimension_pattern = re.compile(r"(?:\w[^\^\/ ]*)(?:\^[0-9])?")

class MeaninglessUnitsException(Exception):
    pass

class DimensionError(Exception):
    pass

class Units(object):
    """Used for dimensional and other analysis."""
    __slots__ = ("_dimensions", "_positive")
    delta_strings = ("delta ", "Δ ")
    @staticmethod
    def parsed_from(unit_string, positive = None):
        "format example: m Kg^2 / s^2"
        
        if positive is None:
            positive = True
            for delta_string in Units.delta_strings:
                if unit_string.startswith(delta_string):
                    unit_string = unit_string[len(delta_string):]
                    positive = False
                    break
        
        dimensions = {}
        for factor, dimension_counts in zip((1,-1), unit_string.split("/")):
            for match in counted_dimension_pattern.finditer(dimension_counts):
                dimension_spec = match.group()
                if "^" in dimension_spec:
                    dimension, count = dimension_spec.split("^")
                else:
                    dimension = dimension_spec
                    count = 1
                count = factor * int(count)
                try:
                    existing_count = dimensions[dimension]
                except KeyError:
                    dimensions[dimension] = count
                else:
                    dimensions[dimension] += count
        return Units(dimensions, positive)

    def __init__(units, dimensions, positive):
        """Example:
        >>> c = Counter({"a": 4, "b": 2})

        """
        for dimension, count in dimensions.iteritems():
            if not isinstance(count, int):
                raise DimensionError(
                    "%s dimension count must be a whole number" % dimension
                )
        units._dimensions = dimensions.copy()
        units._positive = bool(positive)
    
    def iteritems(units):
        return units._dimensions.iteritems()

    def __repr__(units):
        return "%s({%s}, %s)" % (
            units._positive,
            units.__class__.__name__,
            ", ".join(
                map("%r: %r".__mod__, units._dimensions.iteritems())
            )
        )
        
    def __str__(units):
        if not units._dimensions:
            return "(dimensionless)"
        else:
            negative_dimensions = []
            positive_dimensions = []
            for dimension, count in units._dimensions.iteritems():
                if count < 0:
                    negative_dimensions.append((dimension, count))
                else:
                    positive_dimensions.append((dimension, count))
            
            dimension_strings = []
            def dimension_group(group):
                for dimension, count in group:
                    if " " in dimension:
                        dimension_name = "(%s)" % dimension
                    else:
                        dimension_name = dimension
                    if count == 1:
                        dimension_strings.append(dimension_name)
                    else:
                        dimension_strings.append(
                            "%s^%s" % (
                                dimension_name, 
                                #"²³⁴⁵⁶⁷⁸⁹"[count-2]
                                count
                            )
                        )
            dimension_group(positive_dimensions)
            if negative_dimensions:
                dimension_strings.append("/")
                dimension_group(negative_dimensions)
                
            return ["Δ ", ""][units._positive]+(" ".join(dimension_strings))
    
    def match_dimensions_of(units, other_units):
        return (
            isinstance(other_units, WhateverUnitsAreNeeded) or
            units._dimensions == other_units._dimensions
        )
    
    def __eq__(units, other_units):
        return (
            units._dimensions == other_units._dimensions 
            and units._positive == other_units._positive
        )
    
    def __ne__(units, other_units):
        return not units.__eq__(other_units)

    def __add__(units, other_units):
        # signed + signed = signed
        # positive + signed = positive
        # signed + positive = positive
        # positive + positive = positive, but nonsense (used in average)
        return Units(
            units._dimensions,
            units._positive or other_units._positive
        )
    
    def __sub__(units, other_units):
        # signed - signed = signed
        # positive - signed = positive
        # signed - positive = signed, but nonsense
        # positive - positive = signed
        return Units(
            units._dimensions,
            units._positive and not other_units._positive
        )

    def _mul(units, other_units, multiplier):
        result = units._dimensions.copy()
        get = units._dimensions.get
        if not isinstance(other_units, WhateverUnitsAreNeeded):
            for dimension, count in other_units.iteritems():
                result[dimension] = get(dimension, 0) + multiplier * count
                if result[dimension] == 0:
                    del result[dimension]
        return Units(
            result, 
            units._positive and other_units._positive     
        )

    def __mul__(units, other_units):
        # positive * positive = positive
        # positive * signed = signed
        # signed * positive = signed
        # signed * signed = signed, but nonsense
        return units._mul(other_units, 1)

    def __div__(units, other_units):
        # positive / positive = positive
        # positive / signed = signed
        # signed / positive = signed
        # signed / signed = signed 
        return units._mul(other_units, -1)
    
    def __pow__(units, factor):
        # even = positive
        # odd = signed
        # zero is not allowed
        result = {}
        for dimension, count in units._dimensions.iteritems():
            new_count = int(count * factor)
            if new_count != float(count) * float(factor):
                raise DimensionError(
                    "Non-integral %s dimension encountered." % dimension
                )
            result[dimension] = new_count
            if result[dimension] == 0:
                del result[dimension]
        return Units(
            result,
            units._positive
        )

class WhateverUnitsAreNeeded(object):
    def __init__(units, positive = None):
        if positive is None:
            positive = True
        units._positive = positive
    
    def __repr__(units):
        return "(Whatever units are needed)"
     
    def __str__(units):
        return ""
        
    def match_dimensions_of(units, other_units):
        return True
    
    __add__ = __sub__= __mul__ = __div__= __pow__ = \
        lambda units, other_units: other_units
        
    def __eq__(units, other_units):
        return True

Dimensionless = Units({}, positive = True)

from . import Method
units = Method("units")


from . import (
    Addition, Subtraction, Multiplication, Division, Pow,
    operations, aggregations,
    BinaryOperator,
    Average, Sum, Minimum, Maximum, Count, 
    StandardDeviation, Count, Number
)

def binop_units(binop, use_units):
    left_units = units(binop.left)
    right_units = units(binop.right)
    if left_units is not None and right_units is not None:
        use_units(left_units, right_units)
    else:
        binop.units = None

@units.implementation(Addition)
def addition_units(operation):
    def determine_units(left_units, right_units):
        if not left_units.match_dimensions_of(right_units):
            operation.units_error = MismatchedUnits(
                (operation, left_units, right_units)
            )
            operation.units = None
        else:
            operation.units = left_units + right_units
    binop_units(operation, determine_units)
    return operation.units
                
@units.implementation(Subtraction)
def subtract_units(operation):
    def determine_units(left_units, right_units):
        if not left_units.match_dimensions_of(right_units):
            operation.units_error = (
                "Incompatible units: %(left_units)s and %(right_units)s" % locals()
            )
            operation.units = None
        else:
            operation.units = left_units - right_units
    binop_units(operation, determine_units)
    return operation.units

@units.implementation(Multiplication)
def multiply_units(operation):
    binop_units(operation,
        lambda left_units, right_units:
            setattr(operation, "units", left_units * right_units)
    )
    return operation.units

@units.implementation(Division)
def divide_units(operation):
    binop_units(operation,
        lambda left_units, right_units:
            setattr(operation, "units", left_units / right_units)
    )
    return operation.units

@units.implementation(Pow)
def raise_units_to_power(operation):
    def determine_units(left_units, right_units):
        if right_units is WhateverUnitsAreNeeded:
            operation.right_units = right_units = Dimensionless
        if right_units == Dimensionless:
            operation.units = left_units ** operation.right
        else:
            operation.units_error = "Exponents must be dimensionless, of the form n or 1/n"
            operation.units = None

    binop_units(operation, determine_units)
    return operation.units

@units.implementation(Average, Sum, Minimum, Maximum)
def aggregation_units(aggregation):
    aggregation.units = Units(
        {
            aggregation.sample_table.units_name:1
        },
        True # affine
    )
    return aggregation.units
    
@units.implementation(StandardDeviation)
def stddev_determine_units(aggregation):
    aggregation.units = Units(
        {
            aggregation.sample_table.units_name:1
        },
        False # displacement
    )
    return aggregation.units

@units.implementation(Count)
def count_units(count):
    count.units = Dimensionless
    return count.units

# CV would also be constant units

@units.implementation(Number)
def number_units(number):
    return number.units # set in constructor

@units.implementation(int, float)
def primitive_number_units(number):
    return WhateverUnitsAreNeeded




analysis = Method("analysis")

@analysis.implementation(Number)
def Number_analysis(number, out):
    out(number.value, " ", number.units)

@analysis.implementation(*operations)
def Binop_analysis(binop, out):
    def indent(*strings):
        out("    ", *strings)

    out("(")
    analysis(binop.left, indent)

    indent(binop.op)
    
    analysis(binop.right, indent)
    out(")    # ", binop.units or "???")
    if hasattr(binop, "units_error"):
        out("# ", binop.units_error)


@analysis.implementation(*aggregations)
def aggregation_analysis(aggregation, out):
    out(type(aggregation).__name__, "(    # ", aggregation.units or "???")
    def indent(*strings):
        out("    ", *strings)
    indent(str(aggregation.sample_table), ",")
    
    for specification in aggregation.specification:
        indent(specification, ",")
    out(")")

@analysis.implementation(int, float)
def primitive_number_analysis(number, out):
    out(number)
