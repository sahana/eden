# -*- coding: utf-8 -*-

"""
    Climate Data Module

    @author: Mike Amy
"""

from gluon import current
from gluon.contrib.simplejson.ordered_dict import OrderedDict

db = current.db

same = lambda x: x
# keyed off the units field in the sample_table_spec table
units_in_out = {
    "Celsius": {
        "in": lambda celsius: celsius + 273.15,
        "out": lambda kelvin: kelvin - 273.15
    },
    "Fahreinheit": {
        "in": lambda fahreinheit: (fahreinheit + 459.67) + (5.0/9.0),
        "out": lambda kelvin: (kelvin * (9.0/5.0)) - 459.67
    },
    "Kelvin": {
        "in": same,
        "out": same
    },
    
    "mm": {
        "in": same,
        "out": same
    }
}

# date handling

from datetime import date, timedelta
start_year = 2011
start_month_0_indexed = 10
start_date = date(start_year, start_month_0_indexed+1, 11)
start_day_number = start_date.toordinal()

class DateMapping(object):
    def __init__(date_mapper, from_year_month_day, from_date):
        date_mapper.year_month_day_to_time_period = from_year_month_day
        date_mapper.date_to_time_period = from_date

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

from math import floor

def rounded_date_to_month_number(date):
    """This function converts a date to a month number by rounding
    to the nearest 12th of a year.
    
    See also date_to_month_number(year, month)
    """
    timetuple = date.timetuple()
    year = timetuple.tm_year
    day_of_year = timetuple.tm_yday
    month0 = floor(((day_of_year / 365.0) * 12) + 0.5)
    return ((year-start_year) * 12) + (month0) - start_month_0_indexed

print "WARNING: NetCDF imports using unusual date semantics might not work"
monthly = DateMapping(
    from_year_month_day = year_month_to_month_number,
    from_date = date_to_month_number, # Different for different data sets!
)

def date_to_day_number(date):
    return date.toordinal() - start_day_number

def year_month_day_to_day_number(year, month, day):
    return date_to_day_number(date(year, month, day))

daily = DateMapping(
    from_year_month_day = year_month_day_to_day_number,
    from_date = date_to_day_number
)

class Observed(object):
    code = "O"
    
class Gridded(object):
    code = "G"
    
class Projected(object):
    code = "P"

SampleTableTypes = (Observed, Gridded, Projected)

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
    __types = OrderedDict()
    for SampleTableType in SampleTableTypes:
        __types[SampleTableType.code] = SampleTableType
        
    __date_mapper = {
        "daily": daily,
        "monthly": monthly
    }
    __objects = {}
    __names = OrderedDict()

    @staticmethod
    def with_name(name):
        return SampleTable.__names[name]
    
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
        sample_type_code,
    ):
        return SampleTable.__objects[(parameter_name, sample_type_code)]

    @staticmethod
    def add_to_client_config_dict(config_dict):
        data_type_option_names = []
        for SampleTableType in SampleTableTypes:
            data_type_option_names.append(SampleTableType.__name__)                

        config_dict.update(
            data_type_option_names = data_type_option_names,
            parameter_names = SampleTable.__names.keys()
        )
    
    def __init__(
        sample_table, 
        db, 
        name, # please change to parameter_name
        sample_type,
        date_mapping_name,
        field_type,
        units_name,
        id = None
    ):
        assert sample_type in SampleTableTypes
        sample_table.type = sample_type
        sample_table.db = db
        sample_table.parameter_name = name
        sample_table.date_mapping_name = date_mapping_name
        sample_table.date_mapper = SampleTable.__date_mapper[date_mapping_name]
        sample_table.field_type = field_type
        assert units_name in units_in_out.keys(), \
            "units must be one of %s" % units_in_out.keys()
        sample_table.units_name = units_name
        if id is not None:
            sample_table.set_id(id)
    
    def __str__(sample_table):
        return '"%s %s"' % (sample_table.type.__name__, sample_table.parameter_name)
    
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
                    date_mapping = sample_table.date_mapping_name
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

        def complain_that_table_already_exists(
            query, 
            existing_table_name
        ):
            raise Exception(
                "Table for %s %s already exists as '%s'" % (
                    sample_table.sample_type.__name__,
                    sample_table.parameter_name, 
                    existing_table_name
                )
            )
        return sample_table.find(
            not_found = create_table,
            found = complain_that_table_already_exists
        )

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
        sample_table.db.executesql(
            "INSERT INTO %s (time_period, place_id, value) VALUES %s;" % (
                sample_table.table_name,
                ",".join(values)
            )
        )

def init_SampleTable():
    for SampleTableType in SampleTableTypes:
        for sample_table_spec in db(
            db.climate_sample_table_spec.sample_type_code == SampleTableType.code
        ).select(
            orderby = db.climate_sample_table_spec.name
        ):
            sample_type_code = sample_table_spec.sample_type_code
            parameter_name = sample_table_spec.name
            sample_table_types = SampleTable._SampleTable__types
            sample_type = sample_table_types[sample_table_spec.sample_type_code]
            date_mapper = SampleTable._SampleTable__date_mapper
            sample_table = SampleTable(
                name = sample_table_spec.name,
                id = sample_table_spec.id,
                units_name = sample_table_spec.units,
                field_type = sample_table_spec.field_type,
                date_mapping_name = sample_table_spec.date_mapping,
                sample_type = sample_type, 
                db=db
            )
            SampleTable._SampleTable__objects[
                (parameter_name, sample_type_code)
            ] = sample_table
            SampleTable._SampleTable__names["%s %s" % (
                sample_type.__name__, 
                parameter_name
            )] = sample_table
init_SampleTable()

from MapPlugin import MapPlugin
