
s3gis_tests = load_module("tests.unit_tests.modules.s3.s3gis")

def test_OpenStreetMap():
    s3gis_tests.layer_test(
        db,
        db.gis_layer_openstreetmap,
        dict(
            enabled = True,
            name = "test OSM layer",
            url1 = "http://otile1.example.com/tiles/1.0.0/osm/",
            url2 = "http://otile2.example.com/tiles/1.0.0/osm/",
            url3 = "http://otile3.example.com/tiles/1.0.0/osm/",
            attribution = "These are just test tiles <a href='http://www.example.com/' target='_blank'>Test link</a>",
            base = False,
            visible = True,
            zoom_levels = 18
        ),
        "S3.gis.layers_osm[0]",
        {
            "name": u"test OSM layer",
            "url1": u"http://otile1.example.com/tiles/1.0.0/osm/",
            "url2": u"http://otile2.example.com/tiles/1.0.0/osm/",
            "url3": u"http://otile3.example.com/tiles/1.0.0/osm/",
            "isBaseLayer": False,
            "attribution": u"These are just test tiles <a href='http://www.example.com/' target='_blank'>Test link</a>",
            "zoomLevels": 18
        },
        session,
        request,
    )
