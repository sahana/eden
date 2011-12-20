
s3gis_tests = load_module("tests.unit_tests.modules.s3.s3gis")
#s3gis = local_import("s3.s3gis")

def test_TMSLayer():
    s3gis_tests.layer_test(
#        s3gis.TMSLayer,
        db,
        db.gis_layer_tms,
        dict(
            name = "Test TMS",
            description = "Test TMS layer",
            enabled = True,
            created_on = datetime.datetime.now(),
            modified_on = datetime.datetime.now(),
            url = "test://test_TMS",
            layername = "Test TMS layer name",
        ),
        "S3.gis.layers_tms",
        [
            {
                "layername": u"Test TMS layer name", 
                "name": u"Test TMS", 
                "url": u"test://test_TMS", 
                "zoomLevels": 19
            }
        ],
        session,
        request,
    )
