
s3gis_tests = load_module("tests.unit_tests.modules.s3.s3gis")

def test_BingLayer():
    s3gis_tests.layer_test(
        db,
        db.gis_layer_bing,
        dict(
            name = "Test Bing Layer",
            description = "Test Bing layer",
            enabled = True,
            created_on = datetime.datetime.now(),
            modified_on = datetime.datetime.now(),
            aerial_enabled = True,
            road_enabled = True,
            hybrid_enabled = True,
            apikey = "FAKEAPIKEY",
        ),
        "S3.gis.Bing",
        {
            "Aerial": u"Bing Satellite",
            "ApiKey": u"FAKEAPIKEY",
            "Hybrid": u"Bing Hybrid",
            "Road": u"Bing Roads",
        },
        session = session,
        request = request,
    )
