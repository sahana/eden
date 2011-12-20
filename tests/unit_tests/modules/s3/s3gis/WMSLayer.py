
s3gis_tests = load_module("tests.unit_tests.modules.s3.s3gis")

def test_WMSLayer():
    s3gis_tests.layer_test(
        db,
        db.gis_layer_wms,
        dict(
            name = "Test WMS",
            description = "Test WMS layer",
            enabled = True,
            created_on = datetime.datetime.now(),
            modified_on = datetime.datetime.now(),
            url = "test://test_WMS",
            visible = True,
            layers = "test_layers",
        ),
        "S3.gis.layers_wms",
        [
            {
                "layers": u"test_layers", 
                "name": u"Test WMS", 
                "url": u"test://test_WMS"
            }
        ],
        session = session,
        request = request,
    )
