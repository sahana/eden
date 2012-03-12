
# Code generation --------------------------------------------------

from . import *

BinaryOperator.R_only = False

Sum.SQL_function = "SUM"
Average.SQL_function = "AVG"
StandardDeviation.SQL_function = "STDDEV"
Minimum.SQL_function = "MIN"
Maximum.SQL_function = "MAX"
Count.SQL_function = "COUNT"


can_be_SQL = Method("can_be_SQL")
@can_be_SQL.implementation(Number)
def Number_can_be_SQL(number):
    return True

@can_be_SQL.implementation(Addition, Subtraction, Multiplication, Division)
def Binop_can_be_SQL(binop):
    return (not binop.R_only) and can_be_SQL(binop.left) and can_be_SQL(binop.right)

@can_be_SQL.implementation(Pow)
def Binop_can_be_SQL(binop):
    return (not binop.R_only) and can_be_SQL(binop.left)

@can_be_SQL.implementation(*aggregations)
def Aggregation_can_be_SQL(aggregation):
    return True
    


generate_code = Method("generate_code")

@generate_code.implementation(*operations)
def Binop_generate_code(binop, parent_node_id, key, pre, out, post, extra_filter):
    #if can_be_SQL(binop):
    #    out('dbGetQuery(con, "')
    #    SQL(aggregation, key, out)
    #    out('")')
    #else:
    R(binop, parent_node_id, key, pre, out, post, extra_filter)

SQL = Method("SQL")
R = Method("R")

@SQL.implementation(Number)
def number_out(number, key, out, extra_filter):
    out(repr(number.value))

@R.implementation(Number)
@generate_code.implementation(Number)
def number_out(number, parent_node_id, key, pre, out, post, extra_filter):
    out(repr(number.value))


@SQL.implementation(int)
def int_out(number, key, out):
    out(repr(number))

@R.implementation(int)
@generate_code.implementation(int)
def int_out(number, parent_node_id, key, pre, out, post, extra_filter):
    out(repr(number))

@SQL.implementation(Addition, Subtraction, Multiplication, Division)
def BinaryOperator_SQL(binop, key, out, extra_filter):
    out(
        "SELECT left.key as key,",
        " left.value", binop.sql_op, "right.value as value ",
        "FROM ("
    )
    SQL(binop.left, key, out, extra_filter)
    out(") AS left ",
        "JOIN ("
    )
    SQL(binop.right, key, out, extra_filter)
    out(") AS right ",
        "ON left.key = right.key"
    )

@SQL.implementation(Pow)
def BinaryOperator_SQL(binop, key, out, extra_filter):
    out(
        "SELECT left.key as key,",
        "(left.value^ ", str(binop.right), ") as value ",
        "FROM ("
    )
    SQL(binop.left, key, out, extra_filter)
    out(") AS left")

def init_R_interpreter(R, database_settings):
    # Assumes user functions defined for doing these operations on data.frames    
    R("""
    Pow <- function(left, exponent) {
        if (is.numeric(left))
            if (typeof(left$key) == "NULL")
                return (data.frame())
            else 
                return (
                    data.frame(
                        key = left$key,
                        value = left$value ^ exponent
                    )
                )
        else
            return (left ^ exponent)
    }
    AddDataFrameToNumber <- function (dataframe, number) {
        if (typeof(dataframe$key) == "NULL")
            return (data.frame())
        else 
            return (
                data.frame(
                    key = dataframe$key,
                    value = dataframe$value + number
                )
            )
    }
    Addition <- function(left, right) {
        if (is.numeric(left) && is.numeric(right))
            return (left + right)
        if (is.numeric(left) && is.data.frame(right))
            return (AddDataFrameToNumber(right, left))
        if (is.data.frame(left) && is.numeric(right))
            return (AddDataFrameToNumber(left, right))

        if (typeof(left$key) == "NULL" | typeof(right$key) == "NULL" )
            return (data.frame())
        else 
            merged = merge(left, right, by="key")
            return (
                data.frame(
                    key = merged$key,
                    value = merged$value.x + merged$value.y
                )
            )
    }
    Subtraction <- function(left, right) {
        if (is.numeric(left) && is.numeric(right))
            return (left - right)
        if (is.numeric(left) && is.data.frame(right))
            if (typeof(right$key) == "NULL")
                return (data.frame())
            else 
                return (
                    data.frame(
                        key = right$key,
                        value = left - right$value
                    )
                )
        if (is.data.frame(left) && is.numeric(right))
            if (typeof(left$key) == "NULL")
                return (data.frame())
            else 
                return (
                    data.frame(
                        key = left$key,
                        value = left$value - right
                    )
                )

        if (typeof(left$key) == "NULL" | typeof(right$key) == "NULL" )
            return (data.frame())
        else 
            merged = merge(left, right, by="key")
            return (
                data.frame(
                    key = merged$key,
                    value = merged$value.x - merged$value.y
                )
            )
    }
    MultiplyDataFrameByNumber <- function (dataframe, number) {
        if (typeof(dataframe$key) == "NULL")
            return (data.frame())
        else 
            return (
                data.frame(
                    key = dataframe$key,
                    value = dataframe$value * number
                )
            )
    }
    Multiplication <- function(left, right) {
        if (is.numeric(left) && is.numeric(right))
            return (left * right)
        if (is.numeric(left) && is.data.frame(right))
            return (MultiplyDataFrameByNumber(right, left))
        if (is.data.frame(left) && is.numeric(right))
            return (MultiplyDataFrameByNumber(left, right))

        if (typeof(left$key) == "NULL" | typeof(right$key) == "NULL" )
            return (data.frame())
        else 
            merged = merge(left, right, by="key")
            return (
                data.frame(
                    key = merged$key,
                    value = merged$value.x * merged$value.y
                )
            )
    }
    Division <- function(left, right) {
        if (is.numeric(left) && is.numeric(right))
            return (left / right)
        if (is.numeric(left) && is.data.frame(right))
            if (typeof(right$key) == "NULL")
                return (data.frame())
            else 
                return (
                    data.frame(
                        key = right$key,
                        value = left / right$value
                    )
                )
        if (is.data.frame(left) && is.numeric(right))
            if (typeof(left$key) == "NULL")
                return (data.frame())
            else 
                return (
                    data.frame(
                        key = left$key,
                        value = left$value / right
                    )
                )
        if (typeof(left$key) == "NULL" | typeof(right$key) == "NULL" )
            return (data.frame())
        else 
            merged = merge(left, right, by="key")
            return (
                data.frame(
                    key = merged$key,
                    value = merged$value.x / merged$value.y
                )
            )
    }
    """)

    from rpy2.rinterface import RRuntimeError
    try:
        R("library(RPostgreSQL, quietly=TRUE)")
    except RRuntimeError, R_runtime_error:
        message = """%s
R package RPostgreSQL might not be installed.
To install it is a bit tricky:

1.
# export PG_CONFIG=/path/to/your/PostgreSQL/bin/pg_config

2. in an R shell:
> install.packages("RPostgreSQL", type="source")
You may need to select a mirror.
            """  % R_runtime_error
        import sys
        sys.stderr.write(message)
        raise ImportError(message)

    try:
        R("library(multicore, quietly=TRUE)")
    except RRuntimeError, R_runtime_error:
        if "no package called" in R_runtime_error.args[0]:
            raise ImportError(
                """R package multicore is not installed, to install it:

In an R shell:
> install.packages("multicore")
                """
            )
        else:
            raise

    R("""
    single_connection_query <- function(SQL_statement) {
        postgres <- dbDriver("PostgreSQL")
        connection <- dbConnect(
            postgres,
            dbname="%(database)s",
            password="%(password)s",
            user="%(username)s",
            host="%(host)s",
            port="%(port)s"
        )
        result = dbGetQuery(connection, SQL_statement)
        dbDisconnect(connection)
        dbUnloadDriver(postgres)
        return (result)
    }

    """ % database_settings
    )
    
@R.implementation(*operations)
def BinaryOperator_R(binop, parent_node_id, key, pre, out, post, extra_filter):
    out(type(binop).__name__, "(")
    generate_code(binop.left, parent_node_id+"_left", key, pre, out, post, extra_filter)
    out(", ")
    generate_code(binop.right, parent_node_id+"_right", key, pre, out, post, extra_filter)
    out(")")

@generate_code.implementation(
    *aggregations
)
def DSLAggregationNode_generate_code(aggregation, node_id, key, pre, out, post, extra_filter):
    R(aggregation, node_id, key, pre, out, post, extra_filter)

@R.implementation(*aggregations)
def DSLAggregationNode_R(aggregation, parent_node_id, key, pre, out, post, extra_filter):
    # Has to use SQL
    node_id =  parent_node_id+"_"+type(aggregation).__name__
    
    pre(node_id, " <- parallel(single_connection_query('")
    SQL(aggregation, key, pre, extra_filter)
    pre("'\n))\n")
    pre("query_jobs[[length(query_jobs)+1]] <- ", node_id, "\n")
    
    out("query_results[[toString(processID(", node_id, "))]]")

from .. import start_month_0_indexed
@SQL.implementation(*aggregations)
def DSLAggregationNode_SQL(aggregation, key, out, extra_filter):
    """From this we are going to get back a result set with key and value.
    """
    sample_table = aggregation.sample_table
    out("SELECT ", key)

    from_date = aggregation.from_date
    if from_date is not None:
        from_time_period = sample_table.date_mapper.date_to_time_period(from_date)
        #if key == "time_period" and from_time_period:
            #out("- %i" % from_time_period)
    else:
        from_time_period = None
    out(" as key, ",
        aggregation.SQL_function, "(value) as value ",
        'FROM \\"', sample_table.table_name, '\\"'
    )
    filter_strings = []
    if extra_filter:
        filter_strings.append(extra_filter)
    add_filter = filter_strings.append
    month_numbers = aggregation.month_numbers
    if month_numbers is not None and -1 in month_numbers:
        # PreviousDecember handling:
        # shift the month numbers forward by one month and compare against 
        # month filter numbers also shifted forward one month.
        time_period = "(time_period + 1)"
        month_numbers = map((1).__add__, month_numbers)
    else:
        time_period = "time_period"
    if from_time_period is not None:
        add_filter(
            "%(time_period)s >= %(from_date_number)i" % dict(
                time_period = time_period,
                from_date_number = sample_table.date_mapper.date_to_time_period(from_date)
            )
        )
    to_date = aggregation.to_date
    if to_date is not None:
        add_filter(
            "%(time_period)s <= %(to_date_number)i" % dict(
                time_period = time_period,
                to_date_number = sample_table.date_mapper.date_to_time_period(to_date)
            )
        )
    if month_numbers is not None and month_numbers != list(range(0,12)):
        if month_numbers == []:
            add_filter("FALSE")
        else:
            add_filter(
                "((%(time_period)s + 65532 + %(month_offset)i) %% 12) IN (%(month_list)s)" % dict(
                    time_period = time_period,
                    month_offset = start_month_0_indexed,
                    month_list = ",".join(map(str, month_numbers))
                )
            )
    if filter_strings:
        out(
            " WHERE ", 
            " AND ".join(filter_strings)
        )        
    out(" GROUP BY ", key)

def R_Code_for_values(expression, attribute, extra_filter = None):
    pre_output = [
        "function () {\n",
        "query_jobs <- list()\n"
    ]
    extend_pre_output = pre_output.extend
    def pre(*strings):
        extend_pre_output(strings)

    output = [
        # wait for all SQL queries to complete
        "query_results <- collect(jobs=query_jobs, wait=TRUE)\n",
        "result = "
    ]
    extend_output = output.extend
    def out(*strings):
        extend_output(strings)


    post_output = []
    extend_post_output = post_output.extend
    def post(*strings):
        extend_post_output(strings)

    R(expression, "result", attribute, pre, out, post, extra_filter)
    
    post_output.append("return (result)\n")
    post_output.append("}")

    result = "\n".join(
        map(
            "".join, 
            (
                pre_output,
                output,
                post_output
            )
        )
    )
    #import sys
    #sys.stderr.write( result)
    return result
