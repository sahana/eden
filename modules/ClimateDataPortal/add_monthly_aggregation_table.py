#!/usr/bin/python

# this will be used for aggregating data.

# essentially need to:
# create the table as with add_table.py
# execute some SQL to fill it

# e.g. add_monthly_aggregation_table.py Maximum "Rainfall mm" "float"

# should this not be automatic on adding an observed data table?

import ClimateDataPortal

def aggregate(sample_table, Aggregation, db):
    aggregation_function = Aggregation.SQL_function
    aggregate_table = sample_table+"_monthly_"+aggregation_function
    sample_table_name = sample_table
    value_type = "real"
    create_table_sql = """
    DROP TABLE IF EXISTS %(aggregate_table)s;
    
    CREATE TABLE %(aggregate_table)s (
      place_id integer NOT NULL,
      "month" smallint NOT NULL,
      "value" real NOT NULL,
      CONSTRAINT %(aggregate_table)s_primary_key 
          PRIMARY KEY (place_id, month),
      CONSTRAINT %(aggregate_table)s_place_id_fkey 
          FOREIGN KEY (place_id)
          REFERENCES climate_place (id) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE CASCADE
    );
    """ % locals()
    db.executesql(create_table_sql)
    # takes ~ 30 secs
    year_dot_num = ClimateDataPortal.year_month_to_month_number(0, 1)
    start_date_iso = ClimateDataPortal.start_date.isoformat()
    table_name = sample_table
    aggregation_func = Aggregation.SQL_function
    insert_sql = """
    INSERT INTO %(aggregate_table)s (month, place_id, value) 
    SELECT 
        (
            %(year_dot_num)i +
            (EXTRACT(year FROM "subquery"."date") * 12) +
            (EXTRACT(month FROM "subquery"."date") - 1)
        ) as month,
        "subquery"."place_id" as place_id,
        COALESCE (%(aggregation_func)s("subquery"."value"), 0) as value
    FROM (
        SELECT 
            (date '%(start_date_iso)s' + time_period) as "date",
            value,
            place_id
        FROM %(table_name)s
    ) as "subquery"
    GROUP BY month, place_id
    ;
    """ % locals()
    #print insert_sql
    db.executesql(insert_sql)
    
    """
    update "climate_sample_table_12_monthly_stddev"
        SET count = count.value
    FROM 
        "climate_sample_table_12_monthly_count" as "count"
    WHERE 
        "count"."month" = "climate_sample_table_12_monthly_stddev"."month" and
        "count"."place_id" = "climate_sample_table_12_monthly_stddev"."place_id"
    ;
    update "climate_sample_table_12_monthly_stddev"
        SET mean = mean.value
    FROM 
        "climate_sample_table_12_monthly_avg" as "mean"
    WHERE 
        "mean"."month" = "climate_sample_table_12_monthly_stddev"."month" and
        "mean"."place_id" = "climate_sample_table_12_monthly_stddev"."place_id"
    ;
    
    select 
        "stddev"."place_id",
        sqrt(
            (
                SUM(("stddev"."count" - 1) * ("stddev".value ^ 2))
                + SUM("stddev"."count" * ("stddev"."mean" ^ 2))
                - SUM("stddev"."count") * (
                    (
                        SUM("stddev"."count" * "stddev"."mean") / SUM("stddev"."count")
                    ) ^ 2
                )
            ) / (SUM("stddev"."count") - 1)
        )
    FROM 
        "climate_sample_table_12_monthly_stddev" as "stddev"
    GROUP BY
        "stddev"."place_id"
    ;
    """
    db.commit()

from ClimateDataPortal.DSL import aggregations
for sample_table in db(db.climate_sample_table_spec).select():
    for Aggregation in aggregations:
        #print sample_table.name, Aggregation.__name__
        aggregate(
            ClimateDataPortal.sample_table_id(sample_table.id),
            Aggregation, 
            db
        )



def combine_stddev(x, y, ddof = 1):
    # ddof = 1 matches postgres stddev
    mu_x_u_y = (1.0 / (x.count + y.count)) * ((x.count * x.mean) + (y.count * y.mean))
    return math.sqrt(
        (1.0 / (x.count + y.count - ddof)) * (
            ((x.count - ddof)*(x.stddev ** 2)) +
            ((x.count * (x.mean ** 2))) + 
            
            ((y.count - ddof)*(y.stddev ** 2)) +
            ((y.count * (y.mean ** 2))) -
            
            ((x.count + y.count)*(mu_x_u_y**2))
        )
    )
def combine_stddev3(x, y, z, ddof = 1):
    # ddof = 1 matches postgres stddev
    mu_x_u_y_u_z = (1.0 / (x.count + y.count + z.count)) * ((x.count * x.mean) + (y.count * y.mean) + (z.count * z.mean))
    return math.sqrt(
        (1.0 / (x.count + y.count + z.count - ddof)) * (
            ((x.count - ddof)*(x.stddev ** 2))            
            + ((y.count - ddof)*(y.stddev ** 2))
            + ((z.count - ddof)*(z.stddev ** 2))

            + ((z.count * (z.mean ** 2))) 
            + ((y.count * (y.mean ** 2)))
            + ((x.count * (x.mean ** 2)))  

            - ((x.count + y.count + z.count)*(mu_x_u_y_u_z**2))
        )
    )

# aggregate daily into monthly

"""
INSERT INTO "climate_sample_table_11" 
SELECT sub.place_id as place_id, 
(
   ((sub.year-2011) * 12) + 
   ((sub.month-1) - 10)
) as time_period,
sub.value as value
FROM (
    SELECT place_id, 
    Extract('month' from DATE('2011-11-11') + time_period) as month, 
    Extract('year' from DATE('2011-11-11') + time_period) as year,
    AVG(value) as value
    FROM climate_sample_table_1 
    GROUP BY place_id, year, month
) AS sub
"""