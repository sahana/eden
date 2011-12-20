
s3gis_tests = load_module("tests.unit_tests.modules.s3.s3gis")

def test_WFSLayer():
    s3gis_tests.layer_test(
        db,
        db.gis_layer_wfs,
        dict(
            name = "Test WFS",
            description = "Test WFS layer",
            enabled = True,
            created_on = datetime.datetime.now(),
            modified_on = datetime.datetime.now(),
            url = "test://test_WFS",
            visible = True,
        ),
        "S3.gis.layers_wfs",
        [
            {
                "name": u"Test WFS", 
                "url": u"test://test_WFS", 
                
                "featureNS": None, 
                "featureType": None, 
                "schema": None, 
                "title": u"name", 
            }
        ],
        session = session,
        request = request,
    )
