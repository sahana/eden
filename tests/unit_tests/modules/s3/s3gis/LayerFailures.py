
import unittest

s3gis = local_import("s3.s3gis")
test_utils = local_import("test_utils")
s3gis_tests = load_module("tests.unit_tests.modules.s3.s3gis")


class FailingMethod(object):
    def __init__(self, method_spec, method):
        self.LayerClass, self.method_name = method_spec
        self.method = method
    
    def __enter__(self):
        self.method_impl = getattr(self.LayerClass, self.method_name)
        setattr(self.LayerClass, self.method_name, self.method)

    def __exit__(self, type, value, traceback):
        setattr(self.LayerClass, self.method_name, self.method_impl)
        

ExpectSessionWarning = s3gis_tests.ExpectSessionWarning
    
def check_map_accepts_layer_failure(warning):
    # mock logging        
    with ExpectSessionWarning(session, warning):
        test_gis = s3gis.GIS()
        test_gis.show_map(
            catalogue_layers = True
        )

def thrower(exception_message):
    def fail(*a, **kw):
        raise Exception(exception_message)
    return fail

class LayerFailures(unittest.TestCase):
    def setUp(test):
        current.session.s3.debug = False

    def single_record_layer(test, LayerClass):
        layer_type_name = LayerClass.__name__
        warning = "%s not shown due to error" % layer_type_name
        for method_name in ("__init__", "as_javascript"):
            with FailingMethod(
                (LayerClass, method_name),
                thrower(
                    "Test %s.SubLayer %s failure exception" % (
                        layer_type_name,
                        method_name
                    )
                )
            ):
                check_map_accepts_layer_failure(warning)

    def multiple_record_layer(test, LayerClass, table, **data):
        layer_type_name = LayerClass.__name__
        warning = "%s not shown due to error" % layer_type_name
        test.single_record_layer(LayerClass)
        with s3gis_tests.InsertedRecord(
            db,
            table,
            dict(
                data,
                name = "Test "+layer_type_name,
                enabled = True,
                created_on = datetime.datetime.now(),
                modified_on = datetime.datetime.now(),
            )
        ):
            for method_name in ("__init__", "as_dict"):
                with FailingMethod(
                    (LayerClass.SubLayer, method_name),
                    thrower(
                        "Test %s.SubLayer %s failure exception" % (
                            layer_type_name,
                            method_name
                        )
                    )
                ):
                    check_map_accepts_layer_failure(warning)

    def test_google_layer_failure(test):
        test.single_record_layer(s3gis.GoogleLayer)

    def test_yahoo_layer_failure(test):
        test.single_record_layer(s3gis.YahooLayer)

    def test_bing_layer_failure(test):
        test.single_record_layer(s3gis.BingLayer)

    def test_GPX_layer_failure(test):
        test.multiple_record_layer(s3gis.GPXLayer, db.gis_layer_gpx)

    def test_WMS_layer_failure(test):
        test.multiple_record_layer(s3gis.WMSLayer, db.gis_layer_wms)

    def test_geojson_layer_failure(test):
        test.multiple_record_layer(s3gis.GeoJSONLayer, db.gis_layer_geojson)

    def test_GeoRSS_layer_failure(test):
        test.multiple_record_layer(s3gis.GeoRSSLayer, db.gis_layer_georss)

    def test_KML_layer_failure(test):
        test.multiple_record_layer(s3gis.KMLLayer, db.gis_layer_kml)

    def test_TMS_layer_failure(test):
        test.multiple_record_layer(s3gis.TMSLayer, db.gis_layer_tms)

    def test_WFS_layer_failure(test):
        test.multiple_record_layer(s3gis.WFSLayer, db.gis_layer_wfs)

    def test_feature_layer_failure(test):
        test.multiple_record_layer(s3gis.FeatureLayer, db.gis_layer_feature,
            module = "default"
        )

