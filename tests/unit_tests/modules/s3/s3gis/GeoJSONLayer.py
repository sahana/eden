
s3gis_tests = load_module("tests.unit_tests.modules.s3.s3gis")

def test_GeoJSONLayer():
    s3gis_tests.layer_test(
        db,
        db.gis_layer_geojson,
        dict(
            name = "Test GeoJSON",
            description = "Test GeoJSON layer",
            enabled = True,
            created_on = datetime.datetime.now(),
            modified_on = datetime.datetime.now(),
            url = "test://test_GeoJSON",
        ),
        "S3.gis.layers_geojson",
        [
            {
                "marker_height": 34, 
                "marker_image": u"gis_marker.image.marker_red.png", 
                "marker_width": 20, 
                "name": u"Test GeoJSON", 
                "url": u"test://test_GeoJSON"
            }
        ],
        session = session,
        request = request,
    )
