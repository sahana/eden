
ClimateDataPortal = local_import("ClimateDataPortal")
    
def show_usage():
    sys.stderr.write("""Usage:
    %(command)s sample_type parameter_name units field_type date_mapping gridsize
    
parameter_name: a unique name for the table e.g. "Rainfall" "Max Temp"
field_type: any postgres numeric field type e.g. real, integer, "double precision".
units: mm, Kelvin (displayed units may be different)
sample_type: Observed, Gridded or Projected
date_mapping: daily or monthly
gridsize: 0 for no grid, otherwise, spacing in km

e.g. .../add_table.py Observed "Min Temp" Kelvin real daily 25

""" % dict(
    command = "... add_table.py",
))

import sys

try:
    sample_type_name = sys.argv[1]
    parameter_name = sys.argv[2]
    units_name = sys.argv[3]
    field_type = sys.argv[4]
    date_mapping_name = sys.argv[5]
    grid_size = sys.argv[6]
    assert sys.argv[7:] == [], "%s ??" % sys.argv
except:
    show_usage()
    #raise
else:
    def write_message(sample_table_name):
        print "Added", sample_table_name, sample_type_name, parameter_name
        print "  containing", units_name, "values of type", field_type
        
    try:       
        ClimateDataPortal.SampleTable(
            name = parameter_name,
            sample_type = getattr(ClimateDataPortal, sample_type_name),
            units_name = units_name,
            field_type = field_type,
            date_mapping_name = date_mapping_name,
            grid_size = float(grid_size),
            db = db
        ).create(write_message)
    except:
        show_usage()
        raise
