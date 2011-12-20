
s3gis_tests = load_module("tests.unit_tests.modules.s3.s3gis")

def test_GeoRSSLayer():
    # use debug to show up errors
    # without debug, errors get to be turned into session warnings
    # and the layer skipped altogether. No datastructure.
    url = "test://test_GeoRSS"
    current.request.utcnow = datetime.datetime.now()
    
    test_utils.clear_table(db, db.gis_cache)
    
    db.gis_cache.insert(
        modified_on = datetime.datetime.now(),
        source = url
    )
    db.commit()

    current.session.s3.debug = True
    s3gis_tests.layer_test(
        db,
        db.gis_layer_georss,
        dict(
            name = "Test GeoRSS",
            description = "Test GeoRSS layer",
            enabled = True,
            created_on = datetime.datetime.now(),
            modified_on = datetime.datetime.now(),
            url = url,
        ),
        "S3.gis.layers_georss",
        [
            {
                "marker_height": 34, 
                "marker_image": u"gis_marker.image.marker_red.png", 
                "marker_width": 20, 
                "name": u"Test GeoRSS", 
                "url": u"/eden/gis/cache_feed.geojson?cache.source=test://test_GeoRSS"
            }
        ],
        session = session,
        request = request,
    )

test_utils = local_import("test_utils")
s3gis = local_import("s3.s3gis")

def test_no_cached_copy_available():
    test_utils.clear_table(db, db.gis_cache)
    current.request.utcnow = datetime.datetime.now()

    current.session.s3.debug = True
    gis = s3gis.GIS()
    with s3gis_tests.InsertedRecord(
        db,
        db.gis_layer_georss,
        dict(
            name = "Test GeoRSS",
            description = "Test GeoRSS layer",
            enabled = True,
            created_on = datetime.datetime.now(),
            modified_on = datetime.datetime.now(),
            url = "test://test_GeoRSS",
        )
    ):
        with s3gis_tests.ExpectedException(Exception):
            gis.show_map(
                window = True,
                catalogue_toolbar = True,
                toolbar = True,
                search = True,
                catalogue_layers = True,
                projection = 900913,
            )    
