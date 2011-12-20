
s3gis_tests = load_module("tests.unit_tests.modules.s3.s3gis")

def check(debug, scripts):
    with s3gis_tests.Change(
        current.session.s3,
        {
            "debug": debug
        }
    ):
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
        s3gis_tests.check_scripts(
            actual_output,
            scripts,
            request
        )

def test_debug_scripts():
    check(
        True,
        (
            "/%(application_name)s/static/scripts/gis/openlayers/lib/OpenLayers.js",
            "/%(application_name)s/static/scripts/gis/cdauth.js",
            "/%(application_name)s/static/scripts/gis/osm_styles.js",
            "/%(application_name)s/static/scripts/gis/GeoExt/lib/GeoExt.js",
            "/%(application_name)s/static/scripts/gis/GeoExt/ux/GeoNamesSearchCombo.js",
        )
    )

def test_deployment_scripts():
    check(
        False,
        [
            "/%(application_name)s/static/scripts/gis/OpenLayers.js",
            "/%(application_name)s/static/scripts/gis/GeoExt.js",
        ]
    )

