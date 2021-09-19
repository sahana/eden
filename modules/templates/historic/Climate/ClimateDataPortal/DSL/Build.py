

from . import *

Build = Method("Build")

@Build.implementation(Months)
def build(month_filter, dsl_aggregation_node):
    month_numbers = list(month_filter.month_numbers)
    month_numbers.sort()
    dsl_aggregation_node.set_months(month_numbers)

@Build.implementation(From)
def build(from_date, dsl_aggregation_node):
    dsl_aggregation_node.set_from_date(from_date.date)

@Build.implementation(To)
def build(to_date, dsl_aggregation_node):
    dsl_aggregation_node.set_to_date(to_date.date)

@Build.implementation(*aggregations)
def apply_context(aggregation):
    aggregation.sample_table = SampleTable.with_name(aggregation.dataset_name)
    aggregation.from_date = None
    aggregation.to_date = None
    aggregation.month_numbers = None
    for specification in aggregation.specification:
        Build(specification, aggregation)

@Build.implementation(Addition, Subtraction, Multiplication, Division)
def binop_build(binop):
    Build(binop.left)
    Build(binop.right)

@Build.implementation(Pow)
def binop_build(binop):
    Build(binop.left)

def set_months(aggregation, month_numbers):
    if aggregation.month_numbers is not None:
        raise DSLSyntaxError("Months() was specified twice.")
    aggregation.month_numbers = month_numbers
AggregationNode.set_months = set_months

def set_to_date(aggregation, to_date):
    if aggregation.to_date is not None:
        raise DSLSyntaxError("To was specified twice.")
    aggregation.to_date = to_date
AggregationNode.set_to_date = set_to_date

def set_from_date(aggregation, from_date):
    if (aggregation.from_date is not None):
        raise DSLSyntaxError("From was specified twice.")
    aggregation.from_date = from_date
AggregationNode.set_from_date = set_from_date

@Build.implementation(Number)
def Number_build(positive_number):
    pass
