  
from . import *

def Months__str__(month_filter):
    return "Months(%s)" % (
        ", ".join(
            map(
                Months.sequence.__getitem__,
                month_filter.month_numbers
            )
        )
    )
Months.__str__ = Months__str__


def FromDate__str__(from_date):
    original_args = [from_date.year]
    if from_date.month is not None:
        original_args.append(from_date.month)
    if from_date.day is not None:
        original_args.append(from_date.day)
    return "FromDate(%s)" % ", ".join(map(str,original_args))
FromDate.__str__ = FromDate__str__
    

def ToDate__str__(to_date):
    original_args = [to_date.year]
    if to_date.month is not None:
        original_args.append(to_date.month)
    if to_date.day is not None:
        original_args.append(to_date.day)
    return "ToDate(%s)" % ", ".join(map(str,original_args))
ToDate.__str__ = ToDate__str__


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
