
"""
Gridded data is already aggregated by month

therefore we don't have daily gridded data, but this is 
importing to the same basic table type as if it were daily.

So:
Don't make a daily table
Record what monthly aggregations are available
We only use monthly aggregations on the map and chart so

Some statistics won't be available depending on the aggregation of the gridded data.

Rainfall:
SUM -> AVERAGE -> COUNT

We want SUM

Temp:
We want MAX, MIN, 

Or:
  record what time_period means in the table.
  aggregate month tables into year tables
  leave daily tables empty so that we just don't get any values to add
  but the table is ready there in case the values ever turn up.
  
NetCDF data includes units information so need to use this to convert the data.

"""

ClimateDataPortal = local_import("ClimateDataPortal")
InsertChunksWithoutCheckingForExistingReadings = local_import(
    "ClimateDataPortal.InsertChunksWithoutCheckingForExistingReadings"
).InsertChunksWithoutCheckingForExistingReadings

def get_or_create(dict, key, creator):
    try:
        value = dict[key]
    except KeyError:
        value = dict[key] = creator()
    return value

def get_or_create_record(table, query):
    query_terms = []
    for key, value in query.iteritems():
        query_terms.append(getattr(table, key) == value)
    reduced_query = reduce(
        (lambda left, right: left & right),
        query_terms
    )
    records = db(reduced_query).select()
    count = len(records)
    assert count <= 1, "Multiple records for %s" % query
    if count == 0:
        record = table.insert(**query)
        db.commit()
    else:
        record = records.first()
    return record.id

def nearly(expected_float, actual_float):
    difference_ratio = actual_float / expected_float
    return 0.999 < abs(difference_ratio) < 1.001

#class InsertRowsIfNoConflict(object):
#    def __init__(self, database_table_name, db):
#        raise NotImplemented
#        self.database_table = database_table
#    
#    def add_reading(
#        self,
#        time_period,
#        place_id,
#        value
#    ):
#        database_table = self.database_table
#        records = db(
#            (database_table.time_period == time_period) &
#            (database_table.place_id == place_id)
#        ).select(database_table.value, database_table.id)
#        count = len(records)
#        assert count <= 1
#        if count == 0:
#            database_table.insert(
#                time_period = time_period,
#                place_id = place_id,
#                value = value
#            )
#        else:
#            existing = records.first()
#            assert nearly(existing.value, value), (existing.value, value, place_id)
#    
#    def done(self):
#        pass
    
import datetime

def import_climate_readings(
    netcdf_file,
    field_name,
    add_reading,
    converter,
    start_date_time_string = None,
    is_undefined = (lambda x: (-99.900003 < x < -99.9) or (x < -1e8) or (x > 1e8)),
    time_step_string = None,
    month_mapping_string = None,
    skip_places = False
):
    """
    Assumptions:
        * there are no places
        * the data is in order of places
    """
    
    variables = netcdf_file.variables
    if field_name is "?":
        print ("field_name could be one of %s" % variables.keys())
    else:
        month_mapping_string
    
        def to_list(variable):
            result = []
            for i in range(len(variable)):
                result.append(variable[i])
            return result
        
        def iter_pairs(list):
            for index in range(len(list)):
                yield index, list[index]
        
        time = variables["time"]
        times = to_list(time)
        try:
            time_units_string = time.units
        except AttributeError:
            raise Exception("File has no time unit information")
        else:
            parsed_time_step_string, _, parsed_date, parsed_time = time_units_string.split(" ")
            parsed_date_time_string = parsed_date+" "+parsed_time
            if start_date_time_string is not None:
                assert start_date_time_string == parsed_date_time_string
            try:
                start_date_time = datetime.datetime.strptime(
                    parsed_date_time_string,
                    "%Y-%m-%d %H:%M"
                )
            except ValueError:
                start_date_time = datetime.datetime.strptime(
                    parsed_date_time_string,
                    "%Y-%m-%d %H:%M:%S"
                )
            if time_step_string is not None:
                assert time_step_string == parsed_time_step_string
            else:
                time_step_string = parsed_time_step_string
        
        time_step = datetime.timedelta(**{time_step_string: 1})
        
        try:
            lat_variable = variables["lat"]
        except KeyError:
            lat_variable = variables["latitude"]
        lat = to_list(lat_variable)
        
        try:
            lon_variable = variables["lon"]
        except KeyError:
            lon_variable = variables["longitude"]
            
        month_mapping = {
            "rounded": ClimateDataPortal.rounded_date_to_month_number,
            "twelfths": ClimateDataPortal.floored_twelfth_of_a_360_day_year,
            "calendar": ClimateDataPortal.date_to_month_number 
        }[month_mapping_string]
        try:
            tt = variables[field_name]
        except KeyError:
            raise Exception(
                "Can't find %s in %s" % (
                    field_name,
                    variables.keys()
                )
            )
        else:
            # create grid of places
            place_ids = {}
            
            lon = to_list(lon_variable)
            if skip_places:
                for place in db(climate_place.id > 0).select(
                    climate_place.latitude,
                    climate_place.longitude,
                    climate_place.id
                ):
                    place_ids[(
                        round(place.latitude, 6),
                        round(place.longitude, 6)
                    )] = place.id
            else:
                for latitude in lat:
                    for longitude in lon:
                        record = get_or_create_record(
                            climate_place,
                            dict(
                                longitude = longitude,
                                latitude = latitude
                            )
                        )
                        place_ids[(
                            round(latitude, 6), 
                            round(longitude, 6)
                        )] = record
                        #print longitude, latitude, record

            #print "up to:", len(times)
            print "place_id, time_period, value"
            for time_index, time_step_count in iter_pairs(times):
                sys.stderr.write(
                    "%s %s\n" % (
                        time_index,
                        "%i%%" % int((time_index * 100) / len(times))
                    )
                )
                #print time_period
                if month_mapping_string == "twelfths":
                    year_offset = ((time_step * int(time_step_count)).days) / 360.0
                    month_number = int(
                        ClimateDataPortal.date_to_month_number(start_date_time)
                        + (year_offset * 12.0)
                    )
                    #print month_number, year_offset
                else:
                    time_period = start_date_time + (time_step * int(time_step_count))
                    month_number = month_mapping(time_period)
                    #print month_number, time_period
                values_by_time = tt[time_index]
                if len(tt[time_index]) == 1:
                    values_by_time = values_by_time[0]
                for latitude_index, latitude in iter_pairs(lat):
                    values_by_latitude = values_by_time[latitude_index]
                    for longitude_index, longitude in iter_pairs(lon):
                        value = values_by_latitude[longitude_index]
                        if not is_undefined(value):
                            place_id = place_ids[(round(latitude, 6), round(longitude, 6))]
                            converted_value = converter(value)
                            add_reading(
                                time_period = month_number,
                                place_id = place_id,
                                value = converted_value
                            )
        add_reading.done()
        db.commit()

import sys

from Scientific.IO import NetCDF

def main(argv):
    import argparse
    import os
    styles = {
        "quickly": InsertChunksWithoutCheckingForExistingReadings,
    #    "safely": InsertRowsIfNoConflict
    }

    parser = argparse.ArgumentParser(
        description = "Imports climate data from NetCDF file.",
        prog = argv[0],
        usage = """
%(prog)s --NetCDF_file path/to/file.nc --parameter_name <parameter> --style <import style> --field_name <field name> 

e.g. 
python ./run.py %(prog)s --field_name rr --style quickly --parameter_name "Gridded Rainfall mm" --NetCDF_file gridded_rainfall_mm.nc 

        """
    )
    parser.add_argument(
        "--NetCDF_file",
        required = True,
        help="NetCDF file to import."
    )
    parser.add_argument(
        "--parameter_name",
        required = True,
        choices = ClimateDataPortal.SampleTable._SampleTable__names.keys(),
        help="Parameter name, which corresponds to an added table."
    )
    parser.add_argument(
        "--clear_existing_data",
        type = bool,
        default = False,
        help="Truncate database tables first."
    )
    parser.add_argument(
        "--style",
        required = True,
        choices = styles.keys(),
        default = "safely",
        help="""
            quickly: just insert readings into the database
            safely: check that data is not overwritten
        """
    )
    parser.add_argument(
        "--field_name",
        required = True,
        help="""name of netCDF field that holds the data value
    e.g. "tt" or "rr". Type "?", to discover options."""
    )
    parser.add_argument(
        "--units",
        required = True,
        help="""Units the data is in."""
    )
    parser.add_argument(
        "--time_steps",
        choices = ["seconds", "minutes", "hours", "days"],
        help = "Time steps"
    )
    parser.add_argument(
        "--start_date_time",
        help = """Start time, YYYY-MM-DD hh:mm format
    Only required if it cannot be read from the NetCDF file
    e.g. "1970-01-01 00:00"
        """
    )
    parser.add_argument(
        "--month_mapping",
        required = True,
        choices = [
            "rounded",
            "twelfths",
            "calendar"
        ],
        help = """How to map dates to months:
       
        rounded: take later month at nearest month boundary,
        twelfths: A year is taken as 360 days and is divided into 12,
        calendar: Calendar months, i.e. use the actual month of the date.
        """
    )
    parser.add_argument(
        "--skip_places",
        type = bool,
        default = False,
        help = """Skip checking places and creating them if they don't exist.
        Use this if the table has already been imported once.
        """
    )

    args = parser.parse_args(argv[1:])
    sample_table = ClimateDataPortal.SampleTable.with_name(args.parameter_name)
    sample_table.clear()
    db.commit()       
    
    import_climate_readings(
        netcdf_file = NetCDF.NetCDFFile(args.NetCDF_file),
        field_name = args.field_name,
        add_reading = styles[args.style](sample_table),
        converter = ClimateDataPortal.units_in_out[args.units]["in"],
        time_step_string = args.time_steps,
        start_date_time_string = args.start_date_time,
        month_mapping_string = args.month_mapping,
        skip_places = args.skip_places
    )

if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
