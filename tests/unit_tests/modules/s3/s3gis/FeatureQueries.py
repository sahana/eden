
s3gis_tests = load_module("tests.unit_tests.modules.s3.s3gis")
test_utils = local_import("test_utils")

def test_FeatureQueries():
    actual_output = str(
        s3base.GIS().show_map(
            projection = 900913,
            feature_queries = [
                Storage(
                    name = "test_feature_query",
                    marker = 0, # or can be a real marker with id
                    opacity = 0.5,
                    popup_url = "test://test_popup_url",
                    polygon = True,
                    active = True,
                    query = [
                        Storage(
                            lat = 0.1234,
                            lon = 5.4321,
                            name = "'test' feature",
                            id = 12345,
                        )
                    ]
                )
            ]
        )
    )
    
    def found(data):
        expected = {
            "name": u"test_feature_query",
            "url": u"/eden/gis/feature_query.geojson?feature_query.name=test_feature_query_controller_function&feature_query.created_by=None",
            "opacity": 0.5,
        }
        test_utils.assert_equal(data, expected)
        
    test_utils.find_JSON_format_data_structure(
        actual_output,
        "S3.gis.layers_feature_queries[0]",
        found = found,
        not_found= test_utils.not_found,
        cannot_parse_JSON = test_utils.cannot_parse_JSON
    )
