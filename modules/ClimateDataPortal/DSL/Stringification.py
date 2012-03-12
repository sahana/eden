  
from . import *

def Months__str__(month_filter):
    return "Months(%s)" % (
        ", ".join(
            Months.sequence[month_number + 1] 
            for month_number in month_filter.month_numbers
        )
    )
Months.__str__ = Months__str__


def From__str__(from_date):
    original_args = [from_date.year]
    if from_date.month is not None:
        original_args.append(from_date.month)
    if from_date.day is not None:
        original_args.append(from_date.day)
    return "From(%s)" % ", ".join(map(str,original_args))
From.__str__ = From__str__
    

def To__str__(to_date):
    original_args = [to_date.year]
    if to_date.month is not None:
        original_args.append(to_date.month)
    if to_date.day is not None:
        original_args.append(to_date.day)
    return "To(%s)" % ", ".join(map(str,original_args))
To.__str__ = To__str__

def Number__str__(number):
    return "%s %s" % (number.value, number.units)
Number.__str__ = Number__str__

def AggregationNode__str__(aggregation):
    return "".join((
        type(aggregation).__name__, "(\"",
            aggregation.dataset_name, "\", ",
            ", ".join(
                map(str, aggregation.specification)
            ),
        ")"
    ))
AggregationNode.__str__ = AggregationNode__str__

def BinaryOperator__str__(binop):
    return str(binop.left)+" "+binop.op+" "+str(binop.right)
BinaryOperator.__str__ = BinaryOperator__str__
