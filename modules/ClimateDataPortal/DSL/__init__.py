# -*- coding: utf-8 -*-

"""Climate data portal data analysis DSL

For security reasons, this is designed to be a non-Turing complete, 
non-recursive 
(i.e. no function definition) language. 

The DSL needs to be:
* robust (accept various forms of argument),
* fail-fast (no guessing, raise exceptions quickly.), 
* unambiguous (obvious, long names. No abbreviations.),
* readable (simple, english-like syntax).

=> Python DSL
+ allows operators
+ can provide friendly syntax
+ easy to modify
+ can use python parser
! make sure the DSL is checked. only allow what is recognised.


As of November 2011, there are two use-cases:

1. Generating map overlays.
    We have to get one value for each map point.
    There is an implicit requirement to return values by place.
    It may well be useful to be able to use R functions on maps.

2. Generating charts.
    We have to get one value for each point in time.
    There is an implicit requirement to return values by time 
        (or in future, whatever the chart's x dimension is).

We need:

* Flexibility: i.e. easily allow integration of R functions.
    So, let's assume that we are going via R.

* Performance: i.e. use all CPU cores.
    i.e. one per postgres query.
    Postgres uses a process per request, and no threading.
    We can use more as we don't need to worry about transactions.
    We can read from multiple connections in one process whilst 
    (we hope) they are being worked on in others.
    

Meaningless expressions are allowed in the DSL but then 
detected during the dimensional analysis phase. Some types can be inferred.
"""

# This should be moved somewhere else
class Method(object):
    """Allows better functional cohesion in the source.
    Removes possibility of method name conflicts.
    """
    def __init__(method, name):
        method.implementations = {}
        method.name = name
    
    def implementation(method, *classes):
        def accept_implementation(impl):
            for Class in classes:
                method.implementations[Class] = impl
            return impl
        return accept_implementation
    
    def __call__(method, target, *args, **kwargs):
        try:
            return method.implementations[type(target)](target, *args, **kwargs)
        except KeyError:
            raise TypeError(
                "No %s implementation for %s" % (method.name, type(target))
            )

    def implemented_by(method, target):
        return type(target) in method.implementations



class ASTNode(object):
    # don't allow the __r<op>__ forms - everything must be a ASTNode
    def __add__(node, right):
        return Addition(node, right)
        
    def __sub__(node, right):
        if isinstance(right, int):
            right = Number(right)
        return Subtraction(node, right)
        
    def __mul__(node, right):
        return Multiplication(node, right)

    def __div__(node, right):
        return Division(node, right)

    def __pow__(node, exponent):
        return Pow(node, exponent)

class Number(ASTNode):
    def __init__(number, value, units_name = None):
        number.value = float(value)
        if units_name is None:
            number.units = whatever_units_are_needed
        else:
            number.units = Units.parsed_from(units_name)
    
    def __cmp__(number, other_number):
        return number.value - other_number


class BinaryOperator(ASTNode):
    def __init__(binop, left, right):
        binop.left = left
        binop.right = right
    
    def __repr__(binop):
        return repr(binop.left)+binop.op+repr(binop.right)


class Addition(BinaryOperator):
    op = "+"
    
class Subtraction(BinaryOperator):
    op = "-"

class Multiplication(BinaryOperator):
    op = "*"

class Division(BinaryOperator):
    op = "/"

class Pow(BinaryOperator):
    op = "^"

operations = (Addition, Subtraction, Multiplication, Division, Pow)


class Months(object):
    options = {}
    sequence = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December"
    ]
    # + 3 letter versions:
    for month_name, month_number in zip(sequence, range(1,13)):
        options[month_name] = \
        options[month_name[:3]] = \
        options[month_number] = month_number

    def __init__(month_filter, *months):
        month_filter.months = months

class FromDate(object):
    def __init__(from_date, year, month = None, day = None):
        from_date.year = year
        from_date.month = month
        from_date.day = day
        
class ToDate(object):
    def __init__(to_date, year, month = None, day = None):
        to_date.year = year
        to_date.month = month
        to_date.day = day

class AggregationNode(ASTNode):
    """These all take a dataset and aggregate it.
    """
    def __init__(aggregation, dataset_name, *specification):
        aggregation.dataset_name = dataset_name
        aggregation.specification = specification

class Sum(AggregationNode):
    pass

class Average(AggregationNode):
    pass

class StandardDeviation(AggregationNode):
    pass

class Minimum(AggregationNode):
    pass
    
class Maximum(AggregationNode):
    pass
    
class Count(AggregationNode):
    pass

aggregations = (Maximum, Minimum, Average, StandardDeviation, Sum, Count)

from .. import SampleTable, units_in_out
from Units import Dimensionless

# Validating strings and parsing
def parse(expression_string):
    import re
    
    tokens = []
    out = tokens.append
    def out_all(*pieces):
        tokens.extend(pieces)
    
    def write_table_name(scanner, table_name):
        out(table_name)

    def allowed_identifier(scanner, token):
        out(token)
    
    def operator(scanner, token):
        if token == "^":
            out("**")
        else:
            out(token)

    def write_number(scanner, number):
        out(number)
    
    def number_with_units(scanner, token):
        number, units = token.split(None, 1)
        out_all("Number(", number, ",'", units, "')")
    
    def whitespace(scanner, token):
        out(token)

    def parenthesis(scanner, token):
        out(token)
    
    def comma(scanner, token):
        out(token)
    
    allowed_names = {}
    for name in (
        "Sum Average StandardDeviation Minimum Maximum Count "
        "Months FromDate ToDate Number".split()
    ):
        allowed_names[name] = globals()[name]
    for month_name in Months.options.keys():
        if not isinstance(month_name, int):
            allowed_names[month_name] = month_name
    scanner_spec = (
        (r"#.*?\n", whitespace),
        (r'"('+"|".join(SampleTable._SampleTable__names.keys())+')"', write_table_name),
        (r"(%s)(?=\W)" % "|".join(allowed_names.keys()), allowed_identifier),
        (r"\+|\-|\/|\*|\=|\^", operator),
        (r"\(|\)", parenthesis),
        (r",", comma),
        (r"\s+", whitespace),
        (
            r"-?[0-9]+(?:\.[0-9]+)?\s+(?:(?:delta|Δ)\s+)?(?: *(?:%(units)s)(?:\^[0-9])?)* *(?:\/(?: *(?:%(units)s)(?:\^[0-9])?)*)?" % dict(
                units = "|".join(units_in_out.keys())
            ),
            number_with_units
        ),
        (r"-?[0-9]*(\.[0-9]+)?", write_number),
    )
    scanner = re.Scanner(scanner_spec)
    #print scanner_spec
    #print expression_string
    _, remainder = scanner.scan(expression_string)

    if remainder:
        raise SyntaxError(
            "Syntax error near: '"+("".join(remainder))+"'"
        )
    else:
        cleaned_expression_string = "("+("".join(tokens))+")"
        #print cleaned_expression_string
        expression = eval(
            cleaned_expression_string,
            allowed_names
        )
        if check(expression):
            check_analysis_out = []
            def analysis_out(*things):
                check_analysis_out.append("".join(map(str, things)))
            check_analysis(expression, analysis_out)
            raise TypeError(
                "\n".join(check_analysis_out)
            )
        else:
            Build(expression)
            return expression

from Check import check, check_analysis
from Build import Build
from Units import (
    Units,
    units,
    analysis, 
    whatever_units_are_needed,
    MeaninglessUnitsException
)
from CodeGeneration import R_Code_for_values, init_R_interpreter
import Stringification
