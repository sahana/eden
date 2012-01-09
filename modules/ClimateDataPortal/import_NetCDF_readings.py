
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

class InsertRowsIfNoConflict(object):
    def __init__(self, database_table_name, db):
        raise NotImplemented
        self.database_table = database_table
    
    def add_reading(
        self,
        time_period,
        place_id,
        value
    ):
        database_table = self.database_table
        records = db(
            (database_table.time_period == time_period) &
            (database_table.place_id == place_id)
        ).select(database_table.value, database_table.id)
        count = len(records)
        assert count <= 1
        if count == 0:
            database_table.insert(
                time_period = time_period,
                place_id = place_id,
                value = value
            )
        else:
            existing = records.first()
            assert nearly(existing.value, value), (existing.value, value, place_id)
    
    def done(self):
        pass
    
import datetime

def import_climate_readings(
    netcdf_file,
    field_name,
    add_reading,
    converter,
    start_time = datetime.date(1971,1,1),
    is_undefined = lambda x: -99.900003 < x < -99.9
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
        # create grid of places
        place_ids = {}
        
        def to_list(variable):
            result = []
            for i in range(len(variable)):
                result.append(variable[i])
            return result
        
        def iter_pairs(list):
            for index in range(len(list)):
                yield index, list[index]
        
        times = to_list(variables["time"])
        lat = to_list(variables["lat"])
        lon = to_list(variables["lon"])
        for latitude in lat:
            for longitude in lon:
                record = get_or_create_record(
                    climate_place,
                    dict(
                        longitude = longitude,
                        latitude = latitude
                    )
                )
                place_ids[(latitude, longitude)] = record
                #print longitude, latitude, record
        
        try:
            tt = variables[field_name]
        except KeyError:
            raise Exception("Can't find %s in %s" % (field_name, variables.keys()))
        else:
            print "up to:", len(times)
            for time_index, time in iter_pairs(times):
                print time_index, "%i%%" % int((time_index*100) / len(times)) 
                time_period = start_time+datetime.timedelta(hours=time)
                for latitude_index, latitude in iter_pairs(lat):
                    for longitude_index, longitude in iter_pairs(lon):
                        value = tt[time_index][latitude_index][longitude_index]
                        if not is_undefined(value):
                            month_number = ClimateDataPortal.rounded_date_to_month_number(time_period)
                            place_id = place_ids[(latitude, longitude)]
                            converted_value = converter(value)
                            add_reading(
                                time_period = month_number,
                                place_id = place_id,
                                value = converted_value
                            )
        add_reading.done()
        db.commit()
        print 

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

    args = parser.parse_args(argv[1:])
    sample_table = ClimateDataPortal.SampleTable.with_name(args.parameter_name)
    sample_table.clear()
    db.commit()       
    
    import_climate_readings(
        netcdf_file = NetCDF.NetCDFFile(args.NetCDF_file),
        field_name = args.field_name,
        add_reading = styles[args.style](sample_table),
        converter = ClimateDataPortal.units_in_out[units]["in"]
    )

if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
