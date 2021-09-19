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
  This is done by passing everything through a lexer (scanner)


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

def normalised(value):
    if isinstance(value, (int, float)):
        return Number(value)
    else:
        return value

class ASTNode(object):
    def __add__(node, right):
        return Addition(node, normalised(right))
        
    def __radd__(node, left):
        return Addition(normalised(left), node)
        
    def __sub__(node, right):
        return Subtraction(node, normalised(right))
        
    def __rsub__(node, left):
        return Subtraction(normalised(left), node)
        
    def __mul__(node, right):
        return Multiplication(node, normalised(right))

    def __rmul__(node, left):
        return Multiplication(normalised(left), node)

    def __neg__(node):
        return Multiplication(node, Number(-1))

    def __div__(node, right):
        return Division(node, normalised(right))

    def __rdiv__(node, left):
        return Division(normalised(left), node)

    def __pow__(node, exponent):
        return Pow(node, exponent)

class Number(ASTNode):
    def __init__(number, value, units_name = None):
        number.value = float(value)
        if units_name is None:
            number.units = WhateverUnitsAreNeeded()#value >= 0)
        else:
            number.units = Units.parsed_from(units_name)#, value >= 0)
    
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
    """
    Previous December handling:
    
    If previous december is specified, then the aggregation is done on 
    values taken from the previous year's december. Therefore this is affecting
    the generated SQL.
    
    PreviousDecember and December specified together does not make sense. 
    This should be caught in the Months check and also avoided in the UI.
    
    When previous december is specified, this only affects yearly aggregation.
    
    The start date and end date should be from the month before if the 
    month is January/Dec.
    
    The modulus of the months is not/is shifted.
    
    The SQL should look like:
    
    time_period -1
    
    """
    options = {}
    sequence = [
        "PreviousDecember",
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
    for month_name, month_number in zip(sequence, range(0,13)):
        options[month_name] = \
        options[month_number] = month_number
    # + short versions:
    options["PrevDec"] = 0
    for month_name, month_number in zip(sequence[1:], range(1,13)):
        options[month_name[:3]] = month_number

    def __init__(month_filter, *months):
        month_filter.months = months

class From(object):
    def __init__(from_date, year, month = None, day = None):
        from_date.year = year
        from_date.month = month
        from_date.day = day
        
class To(object):
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

class DSLSyntaxError(SyntaxError):
    pass

class DSLTypeError(TypeError):
    pass

# Validating strings and parsing
def parse(expression_string):
    import re
    
    tokens = []
    remainder = []
    current_position = [0] #, 0] # 2D coords
    
    def move(chars):
        current_position[0] += chars
    
    def linefeed():
        move(1)
        #current_position[1] += 1
        #current_position[0] = 0
    
    def out(token):
        tokens.append(token)
    
    def out_all(*pieces):
        tokens.extend(pieces)
    
    def write_table_name(scanner, table_name):
        out(table_name)
        move(len(table_name))

    def allowed_identifier(scanner, token):
        out(token)
        move(len(token))
    
    def operator(scanner, token):
        if token == "^":
            out("**")
        else:
            out(token)
        move(len(token))

    def write_number(scanner, number):
        out(number)
        move(len(number))
    
    def number_with_units(scanner, token):
        pieces = token.split(None, 1)
        if len(pieces) == 1:
            out_all("Number(", pieces[0], ")")
        else:
            number, units = pieces
            out_all("Number(", number, ",'", units, "')")
        move(len(token))
    
    def whitespace(scanner, token):
        out(" ")
        move(len(token))
        
    def newline(scanner, token):
        linefeed()

    def comment(scanner, token):
        out("")
        move(len(token))
        #linefeed()

    def parenthesis(scanner, token):
        out(token)
        move(len(token))
    
    def comma(scanner, token):
        out(token)
        move(len(token))
    
    def anything_else(scanner, token):
        remainder.append((tuple(current_position), token))
        move(len(token))
    
    allowed_names = {}
    for name in (
        "Sum Average StandardDeviation Minimum Maximum Count "
        "Months From To Number".split()
    ):
        # can't guarantee the __name__, use our name
        allowed_names[name] = globals()[name]
    for month_name in Months.options.keys():
        if not isinstance(month_name, int):
            allowed_names[month_name] = month_name
    scanner_spec = (
        (r"\#[^\n]*(?:\n|$)", comment),
        (
            r'"(%(sample_table_names)s)"' % dict(
                sample_table_names = "|".join(
                    map(
                        re.escape,
                        SampleTable._SampleTable__names.keys()
                    )
                )
            ),
            write_table_name
        ),
        (r"(%s)(?=\W)" % "|".join(allowed_names.keys()), allowed_identifier),
        (r"\+|\-|\/|\*|\=|\^", operator),
        (r"\(|\)", parenthesis),
        (r",", comma),
        (r"\n", newline),
        (r"\s+", whitespace),
        (
            r"-?[0-9]+(?:\.[0-9]+)?\s+"
            r"(?:(?:delta|Δ)\s+)?"
            r"(?:"
                r"(?:%(unit)s+\s*)\/(?:\s*%(unit)s+)|" 
                r"(?:%(unit)s+\s*)|"
                r"(?:\/(?:\s*%(unit)s+))"
            r")"
            % dict(
                # e.g. mm^2, mm
                unit = "(?:(?:%s)(?:\^[0-9])?)" % "|".join(units_in_out.keys())
            ),
            number_with_units
        ),
        (r"-?[0-9]+(\.[0-9]+)?", write_number),
        (r"\S+", anything_else),
    )
    scanner = re.Scanner(scanner_spec)
    #print scanner_spec
    #print expression_string
    scanner.scan(expression_string)

    if remainder:
        #print remainder
        position, string = remainder[0]
        exception = SyntaxError(
            "Syntax error near: '"+("".join(string))+"'"
        )
        #exception.offset, exception.lineno = position
        exception.offset, exception.lineno = position[0], 0
        raise exception
    else:
        cleaned_expression_string = ("".join(tokens))
        #print cleaned_expression_string
        try:
            expression = eval(
                cleaned_expression_string,
                allowed_names
            )
        except SyntaxError, syntax_error:
            dsl_syntax_error = DSLSyntaxError()

            dsl_syntax_error.args = syntax_error.args
            dsl_syntax_error.lineno = syntax_error.lineno
            dsl_syntax_error.msg = syntax_error.msg
            dsl_syntax_error.filename = syntax_error.filename
            dsl_syntax_error.message = syntax_error.message
            dsl_syntax_error.text = syntax_error.text
            dsl_syntax_error.offset = syntax_error.offset
            dsl_syntax_error.print_file_and_line = syntax_error.print_file_and_line
            
            dsl_syntax_error.understood_expression = cleaned_expression_string
            raise dsl_syntax_error
        else:
            if check(expression):
                check_analysis_out = []
                def analysis_out(*things):
                    check_analysis_out.append("".join(map(str, things)))
                check_analysis(expression, analysis_out)
                raise DSLTypeError(
                    "\n".join(check_analysis_out)
                )
            else:
                Build(expression)
                return expression

from Units import (
    Units,
    units,
    analysis, 
    WhateverUnitsAreNeeded,
    MeaninglessUnitsException,
    DimensionError
)
from Check import check, check_analysis
from Build import Build
from CodeGeneration import (
    R_Code_for_values,
    init_R_interpreter
)
from GridSizing import grid_sizes
import Stringification
