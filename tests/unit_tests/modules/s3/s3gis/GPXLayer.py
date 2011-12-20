
s3gis_tests = load_module("tests.unit_tests.modules.s3.s3gis")

def test_GPXLayer():
    s3gis_tests.layer_test(
        db,
        db.gis_layer_gpx,
        dict(
            visible = True,            
            name = "Test GPX",
            description = "Test GPX layer",
            enabled = True,
            created_on = datetime.datetime.now(),
            modified_on = datetime.datetime.now(),
        ),
        "S3.gis.layers_gpx",
        [
            {
                "marker_height": 34, 
                "marker_image": u"gis_marker.image.marker_red.png", 
                "marker_width": 20, 
                "name": u"Test GPX", 
                "routes": False, 
                "url": u"/eden/default/download"
            }
        ],
        session = session,
        request = request,
    )
