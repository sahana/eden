
from web2py_env import local_import, db, gis_map_tables

test_utils = local_import("test_utils")
s3gis = local_import("s3.s3gis")

gis_map_tables()

InsertedRecord = test_utils.InsertedRecord
AddedRole = test_utils.AddedRole
ExpectedException = test_utils.ExpectedException
Change = test_utils.Change
ExpectSessionWarning = test_utils.ExpectSessionWarning

def check_scripts(actual_output, scripts, request):
    substitutions = dict(application_name = request.application)
    for script in scripts:
        script_string = "<script src=\"%s\" type=\"text/javascript\"></script>" % (
            script % substitutions
        )
        assert script_string in actual_output


def layer_test(
    db,
    layer_table,
    layer_data,
    data_structure_lhs,
    data_structure_rhs,
    session,
    request,
    check_output = None,
    scripts = [],
):
    with InsertedRecord(db, layer_table, layer_data):
        with AddedRole(session, session.s3.system_roles.MAP_ADMIN):
            actual_output = str(
                s3gis.GIS().show_map(
                    window = True,
                    catalogue_toolbar = True,
                    toolbar = True,
                    search = True,
                    catalogue_layers = True,
                    projection = 900913,
                )
            )
    
    def found(data_structure):
        test_utils.assert_equal(
            data_structure_rhs, data_structure 
        )
        # ok, test scripts
        substitutions = dict(application_name = request.application)
        for script in scripts:
            script_string = "<script src=\"%s\" type=\"text/javascript\"></script>" % (
                script % substitutions
            )
            assert script_string in actual_output
        if check_output:
            check_output(actual_output)
        
    test_utils.find_JSON_format_data_structure(
        actual_output,
        data_structure_lhs,
        found,
        not_found = test_utils.not_found,
        cannot_parse_JSON = test_utils.cannot_parse_JSON
    )
