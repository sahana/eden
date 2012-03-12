
ClimateDataPortal = local_import("ClimateDataPortal")

def drop_table(sample_type_name, parameter_name):
    def write_message(sample_table_name):
        print "Dropped", sample_table_name, sample_type_name, parameter_name
        
    sample_table_name = ClimateDataPortal.SampleTable.matching(
        parameter_name,
        sample_type_code = getattr(ClimateDataPortal, sample_type_name).code
    ).drop(
        write_message
    )

def show_usage():
    sys.stderr.write("""Usage:
    %(command)s sample_type parameter_name 
    
parameter_name: the name of the table
sample_type: Observed, Gridded or Projected
""" % dict(
    command = "... drop_table.py",
))

import sys

try:
    sample_type_name = sys.argv[1]
    parameter_name = sys.argv[2]
    assert sys.argv[3:] == [], sys.argv
except:
    show_usage()
    raise
else:
    try:
        drop_table(
            sample_type_name,
            parameter_name,
        )
    except:
        show_usage()
        raise
