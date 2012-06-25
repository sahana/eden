# -*- coding: utf-8 -*-

"""
    Climate Data Module

    @author: Mike Amy
"""

from datetime import date, timedelta
from math import floor
from calendar import isleap

from gluon import current
from gluon.contrib.simplejson.ordered_dict import OrderedDict

db = current.db

same = lambda x: x
# keyed off the units field in the sample_table_spec table
standard_unit = {
    "in": same,
    "out": same
}
# be careful to use floats for all of these numbers
units_in_out = {
    "Celsius": {
        "in": lambda celsius: celsius + 273.15,
        "out": lambda kelvin: kelvin - 273.15
    },
    "Fahreinheit": {
        "in": lambda fahreinheit: (fahreinheit + 459.67) + (5.0/9.0),
        "out": lambda kelvin: (kelvin * (9.0/5.0)) - 459.67
    },
    "Kelvin": standard_unit,
    "hPa": standard_unit,
    "Pa": {
        "in": lambda pascals: pascals / 100.0,
        "out": lambda hectopascals: hectopascals * 100.0
    },

    "mm": standard_unit,
    "kg m-2 s-1": {
        "in": lambda precipitation_rate: precipitation_rate * 2592000.0,
        "out": lambda mm: mm / 2592000.0
    },
    
    "%": {
        "in": lambda x: x / 100.0,
        "out": lambda x: x * 100.0
    },
    "ratio": standard_unit,
    "m/s": standard_unit,
}

# date handling
start_year = 2011
start_month_0_indexed = 10
start_date = date(start_year, start_month_0_indexed+1, 11)
start_day_number = start_date.toordinal()

class DateMapping(object):
    def __init__(date_mapper, from_year_month_day, from_date, to_date):
        date_mapper.year_month_day_to_time_period = from_year_month_day
        date_mapper.date_to_time_period = from_date
        date_mapper.to_date= to_date

def date_to_month_number(date):
    """This function converts a date to a month number.
    
    See also year_month_to_month_number(year, month)
    """
    return year_month_to_month_number(date.year, date.month)
 
def year_month_to_month_number(year, month, day=None):
    """Time periods are integers representing months in years, 
    from 1960 onwards.
    
    e.g. 0 = Jan 1960, 1 = Feb 1960, 12 = Jan 1961
    
    This function converts a year and month to a month number.
    """
    return ((year-start_year) * 12) + (month-1) - start_month_0_indexed

def month_number_to_year_month(month_number):
    month_number += start_month_0_indexed
    return (month_number / 12)+start_year, ((month_number % 12) + 1)

def month_number_to_date(month_number):
    year, month = month_number_to_year_month(month_number)
    return date(year, month, 1)

def rounded_date_to_month_number(date):
    """This function converts a date to a month number by rounding
    to the nearest 12th of a year.
    
    See also date_to_month_number(year, month)
    """
    timetuple = date.timetuple()
    year = timetuple.tm_year
    day_of_year = timetuple.tm_yday
    month0 = floor(((day_of_year / (isleap(year) and 366.0 or 365.0)) * 12) + 0.5)
    return ((year-start_year) * 12) + (month0) - start_month_0_indexed

def floored_twelfth_of_a_year(date):
    """This function converts a date to a month number by flooring
    to the nearest 12th of a year.
    """
    timetuple = date.timetuple()
    year = timetuple.tm_year
    day_of_year = timetuple.tm_yday
    month0 = floor((day_of_year / (isleap(year) and 366.0 or 365.0)) * 12)
    return ((year-start_year) * 12) + (month0) - start_month_0_indexed

def floored_twelfth_of_a_360_day_year(date):
    """This function converts a date to a month number by flooring
    to the nearest 12th of a 360 day year. Used by PRECIS projection.
    """
    timetuple = date.timetuple()
    year = timetuple.tm_year
    day_of_year = timetuple.tm_yday
    month0 = floor((day_of_year / 360) * 12)
    return ((year-start_year) * 12) + (month0) - start_month_0_indexed

#import logging
#logging.warn("NetCDF imports using unusual date semantics might not work")
monthly = DateMapping(
    from_year_month_day = year_month_to_month_number,
    from_date = date_to_month_number, # Different for different data sets!
    to_date = month_number_to_date
)

def date_to_day_number(date):
    return date.toordinal() - start_day_number

def year_month_day_to_day_number(year, month, day):
    return date_to_day_number(date(year, month, day))

def day_number_to_date(day_number):
    return start_date + timedelta(days=day_number)

daily = DateMapping(
    from_year_month_day = year_month_day_to_day_number,
    from_date = date_to_day_number,
    to_date = day_number_to_date
)

class Observed(object):
    code = "O"
Observed.__name__ = "Observed Station"
    
class Gridded(object):
    code = "G"
Gridded.__name__ = "Observed Gridded"
    
class Projected(object):
    code = "P"

sample_table_types = (Observed, Gridded, Projected)
sample_table_types_by_code = OrderedDict()
for SampleTableType in sample_table_types:
    sample_table_types_by_code[SampleTableType.code] = SampleTableType

class SampleTable(object):
    # Samples always have places and time (periods)
    # This format is used for daily data and monthly aggregated data.
    
    # Performance matters, and we have lots of data, 
    # so unnecessary bytes are shaved as follows: 

    # 1. Sample tables don't need an id - the time and place is the key
    # 2. The smallest interval is one day, so time_period as smallint (65536)
    #    instead of int, allows a 179 year range, from 1950 to 2129. 
    #    Normally we'll be dealing with months however, where this is 
    #    even less of an issue.
    # 3. The value field type can be real, int, smallint, decimal etc. 
    #    Double is overkill for climate data.
    #    Take care with decimal though - calculations may be slower.
    
    # These tables are not web2py tables as we don't want web2py messing with 
    # them. The database IO is done directly to postgres for speed. 
    # We don't want web2py messing with or complaining about the schemas.
    # It is likely we will need spatial database extensions i.e. PostGIS.
    # May be better to cluster places by region.
        
    __date_mapper = {
        "daily": daily,
        "monthly": monthly
    }
    __objects = {}
    __names = OrderedDict()

    @staticmethod
    def with_name(name):
        return SampleTable.__names[name]

    __by_ids = {}
    @staticmethod
    def with_id(id):
        SampleTable_by_ids = SampleTable.__by_ids
        return SampleTable_by_ids[id]
    
    @staticmethod
    def name_exists(name, error):
        if name in SampleTable.__names:
            return True
        else:
            error(
                "Available data sets are: %s" % SampleTable.__names.keys()
            )
            return False

    @staticmethod
    def matching(
        parameter_name,
        sample_type_code
    ):
        try:
            return SampleTable.__objects[(parameter_name, sample_type_code)]
        except KeyError:
            pass
            #print SampleTable.__objects.keys()

    @staticmethod
    def add_to_client_config_dict(config_dict):
        data_type_option_names = []
        for SampleTableType in sample_table_types:
            data_type_option_names.append(SampleTableType.__name__)                

        parameter_names = []
        for name, sample_table in SampleTable.__names.iteritems():
            if sample_table.date_mapping_name == "monthly":
                parameter_names.append(name)
        config_dict.update(
            data_type_option_names = data_type_option_names,
            parameter_names = parameter_names
        )
    
    def __init__(
        sample_table, 
        db, 
        name, # please change to parameter_name
        date_mapping_name,
        field_type,
        units_name,
        grid_size,
        sample_type = None,
        sample_type_code = None,
        id = None
    ):
        parameter_name = name
        assert units_name in units_in_out.keys(), \
            "units must be one of %s" % units_in_out.keys()
        assert sample_type is None or sample_type in sample_table_types
        assert (sample_type is not None) ^ (sample_type_code is not None), \
            "either parameters sample_type or sample_type_code must be set"
        sample_table_type = sample_type or sample_table_types_by_code[sample_type_code]

        if id is not None:
            if id in SampleTable.__by_ids:
                # other code shouldn't be creating SampleTables that already
                # exist. Or, worse, different ones with the same id.
                raise Exception(
                    "SampleTable %i already exists. "
                    "Use SampleTable.with_id(%i) instead." % (id, id)
                )
                #return SampleTable.__by_ids[id]
            else:
                sample_table.set_id(id)
                SampleTable.__by_ids[id] = sample_table

        sample_table.type = sample_table_type
        sample_table.units_name = units_name
        sample_table.parameter_name = parameter_name
        sample_table.date_mapping_name = date_mapping_name
        sample_table.date_mapper = SampleTable.__date_mapper[date_mapping_name]
        sample_table.field_type = field_type
        sample_table.grid_size = grid_size
        sample_table.db = db

        SampleTable.__objects[
            (parameter_name, sample_table.type.code)
        ] = sample_table
        SampleTable.__names["%s %s" % (
            sample_table.type.__name__, 
            parameter_name
        )] = sample_table
    
    def __repr__(sample_table):
        return '%s %s' % (
            sample_table.type.__name__,
            sample_table.parameter_name
        )

    def __str__(sample_table):
        return '"%s"' % repr(sample_table)
    
    @staticmethod
    def table_name(id):
        return "climate_sample_table_%i" % id
    
    def set_id(sample_table,id):
        sample_table.id = id
        sample_table.table_name = SampleTable.table_name(id)

    def find(
        sample_table,
        found,
        not_found 
    ):
        db = sample_table.db
        existing_table_query = db(
            (db.climate_sample_table_spec.name == sample_table.parameter_name) &
            (db.climate_sample_table_spec.sample_type_code == sample_table.type.code)      
        )
        existing_table = existing_table_query.select().first()
        if existing_table is None:
            not_found()
        else:
            found(
                existing_table_query,
                SampleTable.table_name(existing_table.id),
            )
    
    def create(sample_table, use_table_name):
        def create_table():
            db = sample_table.db
            sample_table.set_id(
                db.climate_sample_table_spec.insert(
                    sample_type_code = sample_table.type.code,
                    name = sample_table.parameter_name,
                    units = sample_table.units_name,
                    field_type = sample_table.field_type,
                    date_mapping = sample_table.date_mapping_name,
                    grid_size = sample_table.grid_size
                )
            )
            db.executesql(
                """
                CREATE TABLE %(table_name)s
                (
                  place_id integer NOT NULL,
                  time_period smallint NOT NULL,
                  value %(field_type)s NOT NULL,
                  CONSTRAINT %(table_name)s_primary_key 
                      PRIMARY KEY (place_id, time_period),
                  CONSTRAINT %(table_name)s_place_id_fkey 
                      FOREIGN KEY (place_id)
                      REFERENCES climate_place (id) MATCH SIMPLE
                      ON UPDATE NO ACTION ON DELETE CASCADE
                );
                """ % sample_table.__dict__
            )
            use_table_name(sample_table.table_name)

        def complain_that_table_already_exists(
            query, 
            existing_table_name
        ):
            raise Exception(
                "Table for %s %s already exists as '%s'" % (
                    sample_table.type.__name__,
                    sample_table.parameter_name, 
                    existing_table_name
                )
            )
        return sample_table.find(
            not_found = create_table,
            found = complain_that_table_already_exists
        )
        
    def create_indices(sample_table):
        db = sample_table.db
        for field in (
            "time_period",
            "place_id",
            "value"
        ):
            db.executesql(
                "CREATE INDEX %(table_name)s_%(field)s__idx "
                "on %(table_name)s(%(field)s);" % dict(
                    sample_table.__dict__,
                    field = field
                )
            )
        use_table_name(sample_table.table_name)

    def drop(sample_table, use_table_name):
        db = sample_table.db
        def complain_that_table_does_not_exist():
            raise Exception(
                "%s %s table not found" % (
                    sample_table.sample_type_name,
                    sample_table.parameter_name,
                )
            ) 
        
        def delete_table(
            existing_table_query, 
            existing_table_name,
        ):
            existing_table_query.delete()
            db.executesql(
                "DROP TABLE %s;" % existing_table_name
            )
            db.commit()
            use_table_name(existing_table_name)
        
        return sample_table.find(
            not_found = complain_that_table_does_not_exist,
            found = delete_table
        )

    def clear(sample_table):
        sample_table.db.executesql(
            "TRUNCATE TABLE %s;" % sample_table.table_name
        )

    def insert_values(sample_table, values):
        sql = "INSERT INTO %s (time_period, place_id, value) VALUES %s;" % (
            sample_table.table_name,
            ",".join(values)
        )
        try:
            sample_table.db.executesql(sql)
        except:
            print sql
            raise
    
    def pull_real_time_data(sample_table):
        import_sql = (
            "SELECT AVG(value), station_id, obstime "
            "FROM weather_data_nepal "
            "WHERE parameter = 'T' "
            "GROUP BY station_id, obstime"
            "ORDER BY station_id, obstime;"
        )
        sample_table.cldb.executesql(
            import_sql
        )

    def csv_data(
        sample_table, 
        place_id,
        date_from,
        date_to
    ):
        sample_table_id = sample_table.id
        date_mapper = sample_table.date_mapper
        start_date_number = date_mapper.date_to_time_period(date_from)
        end_date_number = date_mapper.date_to_time_period(date_to)
        
        data = [
            "date,"+sample_table.units_name
        ]
        for record in db.executesql(
            "SELECT * "
            "FROM climate_sample_table_%(sample_table_id)i "
            "WHERE time_period >= %(start_date_number)i "
            "AND place_id = %(place_id)i "
            "AND time_period <= %(end_date_number)i"
            "ORDER BY time_period ASC;" % locals()
        ):
            place_id, time_period, value = record
            date_format = {
                monthly: "%Y-%m",
                daily: "%Y-%m-%d"
            }[date_mapper]
            data.append(
                ",".join((
                    date_mapper.to_date(time_period).strftime(date_format),
                    str(value)
                ))
            )
        data.append("")
        return "\n".join(data)
        
    def get_available_years(
        sample_table
    ):
        years = []
        for (year,) in db.executesql(
            "SELECT sub.year FROM ("
                "SELECT (((time_period + %(start_month_0_indexed)i) / 12) + %(start_year)i)"
                " AS year "
                "FROM climate_sample_table_%(sample_table_id)i "
            ") as sub GROUP BY sub.year;" % dict(
                start_year = start_year,
                start_month_0_indexed = start_month_0_indexed,
                sample_table_id = sample_table.id
            )
        ):
            years.append(year)
        return years

def init_SampleTable():
    """
    """

    table = current.s3db.climate_sample_table_spec
    for SampleTableType in sample_table_types:
        query = (table.sample_type_code == SampleTableType.code)
        rows = db(query).select(orderby=table.name)
        for sample_table_spec in rows:
            sample_type_code = sample_table_spec.sample_type_code
            parameter_name = sample_table_spec.name
            sample_type = sample_table_types_by_code[sample_table_spec.sample_type_code]
            date_mapper = SampleTable._SampleTable__date_mapper
            SampleTable(
                name = sample_table_spec.name,
                id = sample_table_spec.id,
                units_name = sample_table_spec.units,
                field_type = sample_table_spec.field_type,
                date_mapping_name = sample_table_spec.date_mapping,
                sample_type = sample_type,
                grid_size = sample_table_spec.grid_size,
                db = db
            )
init_SampleTable()

from MapPlugin import MapPlugin
