
s3gis_tests = load_module("tests.unit_tests.modules.s3.s3gis")
test_utils = local_import("test_utils")

yahoo_layer = dict(
    name = "Test Yahoo Layer",
    description = "Test Yahoo",
    enabled = True,
    created_on = datetime.datetime.now(),
    modified_on = datetime.datetime.now(),
    satellite_enabled = True,
    maps_enabled = True,
    hybrid_enabled = True,
    apikey = "FAKEAPIKEY",
)

def test_YahooLayer():
    s3gis_tests.layer_test(
        db,
        db.gis_layer_yahoo,
        yahoo_layer,
        "S3.gis.Yahoo",
        {
            "Hybrid": u"Yahoo Hybrid",
            "Maps": u"Yahoo Maps",
            "Satellite": u"Yahoo Satellite",
        },
        session = session,
        request = request,
    )


def test_yahoo_scripts():
    with s3gis_tests.InsertedRecord(db, db.gis_layer_yahoo, yahoo_layer):
        with s3gis_tests.AddedRole(session, session.s3.system_roles.MAP_ADMIN):
            actual_output = str(
                s3base.GIS().show_map(
                    catalogue_layers = True,
                    projection = 900913,
                )
            )
            s3gis_tests.check_scripts(
                actual_output,
                [
                    "http://api.maps.yahoo.com/ajaxymap?v=3.8&amp;appid=FAKEAPIKEY"
                ],
                request
            )
