import datetime

from . import *

check = Method("check")
# checks arguments are correct type and in range only.

def month_number_from_arg(month, error):
    try:
        month_number = Months.options[month]
    except KeyError:
        error(
            "Months should be e.g. Jan/January or numbers "
            "in range 1 (January) to 12 (Dec), not %s" % month
        )
        return 1
    else:
        return month_number

def month_filter_number_from_arg(month, error):
    try:
        month_number = Months.options[month]
    except KeyError:
        error(
            "Months should be e.g. PrevDec/PreviousDecember/Jan/January or numbers "
            "in range 0 (PreviousDecember) to 12 (Dec), not %s" % month
        )
        return 1
    else:
        return month_number

@check.implementation(Months)
def Months_check(month_filter):
    month_filter.errors = []
    error = month_filter.errors.append
    month_filter.month_numbers = month_numbers = list()
    for month in month_filter.months:                
        month_number = month_number_from_arg(month, error) - 1
        if month_number in month_filter.month_numbers:
            error(
                "%s was added more than once" % month_sequence[month_number]
            )
        month_filter.month_numbers.append(month_number)
    if (
        Months.options["PreviousDecember"] - 1 in month_numbers and 
        Months.options["December"] - 1 in month_numbers
    ):
        error(
            "It doesn't make sense to aggregate with both PreviousDecember and "
            "December. Please choose one or the other."
        )
    return month_filter.errors

@check.implementation(From)
def From_check(from_date):
    from_date.errors = []
    error = from_date.errors.append
    year = from_date.year
    if from_date.month is None:
        month = 1
    else:
        month = from_date.month
    if from_date.day is None:
        day = 1
    else:
        day = from_date.day
    month_number = month_number_from_arg(month, error)
    if not isinstance(year, int):
        error("Year should be a whole number")
    if not isinstance(day, int):
        error("Day should be a whole number")
    if not (1900 < year < 2500):
        error("Year should be in range 1900 to 2500")
    try:
        from_date.date = datetime.date(year, month_number, day)
    except:
        error("Invalid date: datetime.date(%i, %i, %i)" % (year, month_number, day))
    return from_date.errors

import calendar

@check.implementation(To)
def To_check(to_date):
    to_date.errors = []
    error = to_date.errors.append
    year = to_date.year
    if to_date.month is None:
        month = 12
    else:
        month = to_date.month
    if to_date.day is None:
        day = -1
    else:
        day = to_date.day
    if not isinstance(year, int):
        error("Year should be a whole number")
    if not isinstance(day, int):
        error("Day should be a whole number")
    if not (1900 < year < 2500):
        error("Year should be in range 1900 to 2500")
    month_number = month_number_from_arg(month, error)
    if day is -1:
        # use last day of month
        _, day = calendar.monthrange(year, month_number)
    try:
        to_date.date = datetime.date(year, month_number, day)
    except ValueError:
        error("Invalid date: datetime.date(%i, %i, %i)" % (year, month_number, day))
    return to_date.errors

@check.implementation(Addition, Subtraction, Multiplication, Division)
def Binop_check(binop):
    binop.errors = []
    left = check(binop.left)
    right = check(binop.right)
    return left or right

@check.implementation(Pow)
def PowRoot_check(binop):
    binop.errors = []
    error = binop.errors.append
    exponent = binop.right
    if not isinstance(exponent, int) or exponent == 0:
        error("Exponent should be a positive, non-zero number.")
    return check(binop.left) or binop.errors

@check.implementation(*aggregations)
def Aggregation_check(aggregation):
    aggregation.errors = []
    def error(message):
        aggregation.errors.append(message)
    allowed_specifications = (To, From, Months)
    specification_errors = False
    if not isinstance(aggregation.dataset_name, str):
        error("First argument should be the name of a data set enclosed in "
                "parentheses. ")
    else:
        if SampleTable.name_exists(aggregation.dataset_name, error):
            aggregation.sample_table = SampleTable.with_name(aggregation.dataset_name)
    for specification in aggregation.specification:
        if not isinstance(specification, allowed_specifications):
            error(
                "%(specification)s cannot be used inside "
                "%(aggregation_name)s(...).\n"
                "Required arguments are table name: %(table_names)s.\n"
                "Optional arguments are %(possibilities)s." % dict(
                    specification = specification,
                    aggregation_name = aggregation.__class__.__name__,
                    table_names = ", ".join(
                        map(
                            '"%s %s"'.__mod__,
                            climate_sample_tables
                        )
                    ),
                    possibilities = ", ".join(
                        Class.__name__+"(...)" for Class in allowed_specifications
                    )
                )
            )
        specification_errors |= bool(check(specification))
    return aggregation.errors or specification_errors


def Units_check_number(units, value, error):
    if units._positive and value < 0:
        error(
            "Can't guess whether negative numbers without 'delta' are deltas. "
            "Specify the number as a delta e.g. '%s delta mm' "
            "or make it positive." % value
        )
Units.check_number = WhateverUnitsAreNeeded.check_number = Units_check_number

@check.implementation(Number)
def Number_check(number):
    number.errors = []
    number.units.check_number(
        number.value,
        number.errors.append
    )
    return number.errors

check_analysis = Method("check_analysis")

@check_analysis.implementation(Number)
def Number_check_analysis(number, out):
    out(number.value)
    if number.errors:
        out("# ^ ", ", ".join(number.errors))

@check_analysis.implementation(From, To)
def Date_check_analysis(date_spec, out):
    out("%s," % date_spec)
    if date_spec.errors:
        out("# ^ ", ", ".join(date_spec.errors))

@check_analysis.implementation(Months)
def Months_check_analysis(months, out):
    out("%s," % months)
    if months.errors:
        out("# ^ ", ", ".join(months.errors))

@check_analysis.implementation(*operations)
def Binop_check_analysis(binop, out):
    def indent(*strings):
        out("    ", *strings)

    out("(")
    check_analysis(binop.left, indent)

    indent(binop.op)
    
    check_analysis(binop.right, indent)
    out(")")
    if binop.errors:
        out("# ^ ", ", ".join(binop.errors))


@check_analysis.implementation(*aggregations)
def aggregation_check_analysis(aggregation, out):
    out(type(aggregation).__name__, "(")
    def indent(*strings):
        out("    ", *strings)
    indent(str(aggregation.sample_table), ",")
    
    for specification in aggregation.specification:
        check_analysis(specification, indent)
    out(")")
    if aggregation.errors:
        out("# ^ ", ", ".join(aggregation.errors))

@check_analysis.implementation(int, float)
def primitive_number_check_analysis(number, out):
    out(number)

        