#!/usr/bin/python

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


class Readings(object):
    "Stores a set of readings for a single place"
    def __init__(
        self,
        place_id,
        missing_data_marker,
        converter,
        writer,
        time_period,
        maximum = None,
        minimum = None,
    ):
        self.missing_data_marker = missing_data_marker
        self.maximum = maximum
        self.minimum = minimum
        self.converter = converter
        self.place_id = place_id
        self.writer = writer
        self.aggregated_values = {}
        self.time_period = time_period
        
    def __repr__(self):
        return "%s for place %i" % (
            self.writer,
            self.place_id
        )
     
    def add_reading(self, year, month, day, reading, out_of_range):
        if reading != self.missing_data_marker:
            reading = self.converter(reading)
            if (
                (self.minimum is not None and reading < self.minimum) or
                (self.maximum is not None and reading > self.maximum)
            ):
                out_of_range(reading)
            else:
                self.writer(
                    self.time_period(year, month, day),
                    self.place_id,
                    reading
                )

    def done(self):
        self.writer.done()
        
def import_tabbed_readings(
    folder,
    start_station,
    end_station,
    suffix,
    prefix,
    fields,
    clear_existing_data,
    separator,
    missing_data_marker
):
    """
    Expects a folder containing files with name rtXXXX.txt
    
    each file contains lines of the form e.g.:
1978\t1\t1\t0\t-99.9\t-99.9

representing year, month, day, rainfall(mm), minimum and maximum temperature
    """
    import os
    assert os.path.isdir(folder), "%s is not a folder!" % folder
    Observed = ClimateDataPortal.sample_codes["Observed"]
    
    from decimal import Decimal
    import datetime
    
    available_tables = {}
    for sample_table_spec in db(db.climate_sample_table_spec).select():
        if sample_table_spec.sample_type_code == Observed:
            available_tables[sample_table_spec.name] = ClimateDataPortal.sample_table_id(
                sample_table_spec.id
            )
    field_order = []
    
    def readings_lambda(sample_table, input_units):
        conversion = ClimateDataPortal.units_in_out[input_units]["in"]
        return (lambda missing_data_marker, converter, place_id:
            Readings(
                place_id,
                missing_data_marker = missing_data_marker,
                converter = (lambda value: conversion(float(value))),
                time_period = ClimateDataPortal.year_month_day_to_day_number,
                maximum = None,
                minimum = None,
                writer = InsertChunksWithoutCheckingForExistingReadings(sample_table, db)
            )
        )
    date_format = {}
    field_positions = []
    
    for field, position in zip(fields, range(len(fields))):
        if field is not "UNUSED":
            if field in ("year", "month", "day"):
                date_format[field+"_pos"] = position
            else:
                field, input_units = field.rsplit(" ", 1)
                try:
                    sample_table = available_tables[field]
                except KeyError:
                    raise Exception(
                        "'%s' not recognised, available options are: "
                        "year, month, day, %s\n"
                        "You can add new tables using add_table.py" % (
                            field,
                            ", ".join(map("\"%s\"".__mod__, available_tables.keys()))
                        )
                    )
                else:
                    if clear_existing_data:
                        print "Clearing "+sample_table
                        sample_table.clear()
                    field_positions.append(
                        (readings_lambda(sample_table, input_units), position)
                    )
    
    for field in ("year", "month", "day"):
        assert field+"_pos" in date_format, "%s is not specified in --fields" % field

    query_terms = []
    if start_station is not None:
        query_terms.append(climate_station_id.station_id >= start_station)
    if end_station is not None:
        query_terms.append(climate_station_id.station_id <= end_station)
    if not query_terms:
        query = climate_station_id
    else:
        import operator
        query = reduce(operator.and_, query_terms)
    
    stations = list(db(query).select())
    if stations:
        for station in stations:
            station_id = station.station_id
            print station_id
            data_file_path = os.path.join(
                folder,
                (prefix+"%04i"+suffix) % station_id
            )
            if not os.path.exists(data_file_path):
                print "%s not found" % data_file_path
            else:
                variable_positions = []
                for field, position in field_positions:
                    variable_positions.append(
                        (
                            field(
                                missing_data_marker = missing_data_marker,
                                converter = Decimal,
                                place_id = station.id
                            ),
                            position
                        )
                    ) 
                import_data_in_file(
                    data_file_path,
                    tuple(variable_positions),
                    separator,
                    **date_format
                )                
            db.commit()
    else:
        print "No stations! Import using import_stations.py"

def out_of_range(year, month, day, reading):
    print "%s-%s-%s: %s out of range" % (
        year, month, day, reading
    )

def import_data_row(year, month, day, data):
    for variable, field_string in data:
        variable.add_reading(
            year, month, day,
            field_string,
            out_of_range = out_of_range 
        )

def import_data_in_file(
    data_file_path,
    variable_positions,
    separator,
    year_pos,
    month_pos,
    day_pos,
):
#    print variables
    import decimal
    try:
        line_number = 1
        for line in open(data_file_path, "r").readlines():
            if line:
                field_strings = line.split(separator)
                if field_strings.__len__() > 0:
                    try:                        
                        field = field_strings.__getitem__
                        import_data_row(
                            int(field(year_pos)),
                            int(field(month_pos)),
                            int(field(day_pos)),
                            tuple((variable, field(position)) for variable, position in variable_positions)
                        )
                    except (IndexError, ValueError, decimal.InvalidOperation), exception:
                        print line, "line", line_number, ":", exception
            line_number += 1
        for variable, position in variable_positions:
            variable.done()
    except NotImplemented:
        print line
        raise

def main(argv):
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description = "Imports observed climate data from tab-delimited files in a folder.",
        prog= argv[0],
        usage="""

<web2py preamble to run script> \\
  %(prog)s \\
  --folder path_to/folder [options]

Use flag -h | --help for extra help on options.

The file names must follow a convention of prefix + station_id + suffix.
  e.g.: 
  path_to
  `--folder
     |--rt0100.txt
     |--rt0101.txt
     |--...
     `--rt9999.txt

  * Other files in this folder will not be read.
  * Files not corresponding to imported stations will not be read.
  * You must add tables for the data being import before it can be imported. 
    Use add_table.py to do this.

Examples: *(IN ROOT OF APP FOLDER)*

  Import all files in a folder, clearing existing data :

    python ./run.py \\
      %(prog)s \\
      --folder path_to/folder --clear_existing_data \\
      --fields year month day "Rainfall mm" "Max Temp C" "Min Temp C"

  Import a range of stations:

    python ./run.py \\
      %(prog)s \\
      --folder path_to/folder --from 0 --to 500 \\
      --fields year month day "Rainfall mm" "Max Temp C" "Min Temp C"

  Only import Rainfall:

    python ./run.py \\
      %(prog)s \\
      --folder path_to/folder \\
      --fields year month day "Rainfall mm" UNUSED UNUSED
""")

    parser.add_argument(
        "--folder",
        required = True,
        help="Folder in which to search for files."
    )
    parser.add_argument(
        "--clear_existing_data",
        help="Truncate database tables first."
    )
    parser.add_argument(
        "--start_station",
        type=int,
        default = None,
        help="Station number to start from."
    )
    parser.add_argument(
        "--end_station",
        type=int,
        default = None,
        help="""Station number to end on 
        (inclusive, i.e. import data from this station's file too)."""
    )
    parser.add_argument(
        "--prefix",
        default = "rt",
        help="File name prefix e.g. '%(default)s' (default)"
    )
    parser.add_argument(
        "--suffix",
        default = ".txt",
        help="File name suffix e.g. '%(default)s' (default)."
    )
    parser.add_argument(
        "--separator",
        default = None,
        help="Field separator e.g. '\t' (default is None - any whitespace)."
    )
    parser.add_argument(
        "--missing_data_marker",
        default = "-99.9",
        help = """Missing data marker. 
        Interpret this as missing data and do not import anything for that date.
        """
    )
    parser.add_argument(
        "--fields",
        required = True,
        nargs = "+",
        help="""List of fields in file, e.g.:
        year month day "Rainfall mm" "Max Temp Celsius" "Min Temp Celsius"
        year, month and day are used to parse the date.
        The other fields name tables to import data into, mapping by position.
        All fields must be accounted for. Any unused fields should be marked as UNUSED.
        """
    )

    args = parser.parse_args(argv[1:])
    kwargs = {}
    for key, value in args.__dict__.iteritems():
        if not key.startswith("_"):
            kwargs[key] = value

    import_tabbed_readings(**kwargs)

if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
