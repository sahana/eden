
ClimateDataPortal = local_import("ClimateDataPortal")

def add_table(
    sample_type_name,
    parameter_name,
    units_name,
    value_type
):
    def write_message(sample_table_name):
        print "Added", sample_table_name, sample_type_name, parameter_name
        print "  containing", units_name, "values of type", value_type
    
    ClimateDataPortal.SampleTable(
        parameter_name = parameter_name,
        sample_type_name = sample_type_name,
        units_name = units_name,
        value_type = value_type,
        db = db
    ).create(write_message)
    
def show_usage():
    sys.stderr.write("""Usage:
    %(command)s sample_type parameter_name units value_type
    
parameter_name: a unique name for the table e.g. "Rainfall" "Max Temp"
value_type: any postgres numeric field type e.g. real, integer, "double precision".
units: mm, Kelvin (displayed units may be different)
sample_type: Observed, Gridded or Projected

e.g. .../add_table.py Observed "Min Temp" Kelvin real

""" % dict(
    command = "... add_table.py",
))

import sys

try:
    sample_type = sys.argv[1]
    parameter_name = sys.argv[2]
    units = sys.argv[3]
    value_type = sys.argv[4]
    assert sys.argv[5:] == [], sys.argv
except:
    show_usage()
    #raise
else:
    try:
        add_table(
            sample_type,
            parameter_name,
            units,
            value_type
        )
    except:
        show_usage()
        raise
