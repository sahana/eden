
s3gis_tests = load_module("tests.unit_tests.modules.s3.s3gis")

def test_FeatureLayer():
    s3gis_tests.layer_test(
        db,
        db.gis_layer_feature,
        dict(
            id = 1,
            name = "Test feature",
            module = "default"
        ),
        "S3.gis.layers_features",
        [
            {
                "marker_height": 34, 
                "marker_image": u"gis_marker.image.marker_red.png", 
                "marker_width": 20, 
                "name": u"Test feature", 
                "url": u"/eden/controller/default.geojson?layer=1"
            }
        ],
        session,
        request,
    )
