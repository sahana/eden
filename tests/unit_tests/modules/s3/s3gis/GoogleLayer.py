
s3gis_tests = load_module("tests.unit_tests.modules.s3.s3gis")
test_utils = local_import("test_utils")

google_layer = dict(
    name = "Test Google Layer",
    description = "Test Google layer",
    enabled = True,
    created_on = datetime.datetime.now(),
    modified_on = datetime.datetime.now(),
    satellite_enabled = True,
    maps_enabled = True,
    hybrid_enabled = True, 
    mapmaker_enabled = True, 
    mapmakerhybrid_enabled = True,
    earth_enabled = True,
    streetview_enabled = True,
    apikey = "FAKEAPIKEY",
)

def test_GoogleLayer():
    def check_output(actual_output):
        script = "\n".join((
            "<script type=\"text/javascript\"><!--",
            "google && google.load('earth', '1');",
            "//--></script>",
        ))
        assert script in actual_output
    s3gis_tests.layer_test(
        db,
        db.gis_layer_google,
        google_layer,
        "S3.gis.Google",
        {
            "Earth": u"Switch to 3D",
            "Hybrid": u"Google Hybrid",
            "MapMaker": u"Google MapMaker",
            "MapMakerHybrid": u"Google MapMaker Hybrid",
            "Maps": u"Google Maps",
            "Satellite": u"Google Satellite",
        },
        session = session,
        request = request,
        check_output = check_output
    )

def check_scripts(debug, scripts):
    with s3gis_tests.Change(current.session.s3, {"debug": debug}):
        with s3gis_tests.InsertedRecord(
            db,
            db.gis_layer_google,
            google_layer
        ):
            with s3gis_tests.AddedRole(session, session.s3.system_roles.MAP_ADMIN):
                actual_output = str(
                    s3base.GIS().show_map(
                        window = True,
                        catalogue_toolbar = True,
                        toolbar = True,
                        search = True,
                        catalogue_layers = True,
                        projection = 900913,
                    )
                )
                s3gis_tests.check_scripts(actual_output, scripts, request)

def test_google_deployment_scripts():
    check_scripts(
        False,
        [
            "http://maps.google.com/maps?file=api&amp;v=2&amp;key=FAKEAPIKEY",
            "http://www.google.com/jsapi?key=FAKEAPIKEY",
        ]
    )

def test_debug_scripts():
    check_scripts(
        True,
        [
            "http://maps.google.com/maps?file=api&amp;v=2&amp;key=FAKEAPIKEY",
            "http://www.google.com/jsapi?key=FAKEAPIKEY",
            "/%(application_name)s/static/scripts/gis/gxp/widgets/GoogleEarthPanel.js",
        ]
    )
