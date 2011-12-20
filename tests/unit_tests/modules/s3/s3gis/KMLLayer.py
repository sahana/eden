
s3gis_tests = load_module("tests.unit_tests.modules.s3.s3gis")
s3gis = s3gis_tests.s3gis

def test_KMLLayer():
    current.session.s3.debug = True
    current.request.utcnow = datetime.datetime.now()
    s3gis_tests.layer_test(
        db,
        db.gis_layer_kml,
        dict(
            name = "Test KML",
            description = "Test KML layer",
            enabled = True,
            created_on = datetime.datetime.now(),
            modified_on = datetime.datetime.now(),
            url = "test://test_KML",
        ),
        "S3.gis.layers_kml",
        [
            {
                "marker_height": 34, 
                "marker_image": u"gis_marker.image.marker_red.png", 
                "marker_width": 20, 
                "name": u"Test KML", 
                # this shows that caching is OK:
                "url": u"/eden/default/download/gis_cache2.file.Test_20KML.kml"
            }
        ],
        session = session,
        request = request,
    )

def test_KMLCaching_not_possible():
    import os.path
    import sys
    
    class Mock(object):
        pass
    mock_stderr = Mock()
    buffer = []
    def mock_write(error_message):
        buffer.append(error_message)
    mock_stderr.write = mock_write
    
    with s3gis_tests.Change(
        os.path,
        {
            "exists": lambda *a, **kw: False
        }
    ):
        with s3gis_tests.Change(
            sys,
            {
                "stderr": mock_stderr
            }
        ):
            with s3gis_tests.Change(
                current.session.s3,
                {
                    "debug": False
                }
            ):
                kml_layer = s3gis.KMLLayer(s3gis.GIS())
                js = kml_layer.as_javascript()
                
                assert session.error.startswith(
                    "GIS: KML layers cannot be cached: "
                )
                assert "GIS: KML layers cannot be cached:" in buffer[0]
