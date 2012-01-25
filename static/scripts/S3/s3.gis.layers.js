/**
 * S3 GIS Layers
 * Used by the Map (modules/s3gis.py)
 * For Production usage gets assembled into s3.gis.min.js
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

/* Global vars */
// Layers
S3.gis.layers_all = new Array();
S3.gis.format_geojson = new OpenLayers.Format.GeoJSON();
S3.gis.dirs = new Array();

// Add Layers from the Catalogue
function addLayers() {
    /* Base Layers */
    // OSM
    if (S3.gis.layers_osm) {
        for (i = 0; i < S3.gis.layers_osm.length; i++) {
            addOSMLayer(S3.gis.layers_osm[i]);
        }
    }
    // Google (generated server-side in s3gis.py)
    try {
        addGoogleLayers();
    } catch(err) {};
    // Bing
    if (S3.gis.Bing) {
        addBingLayers();
    }
    // TMS
    if (S3.gis.layers_tms) {
        for (i = 0; i < S3.gis.layers_tms.length; i++) {
            addTMSLayer(S3.gis.layers_tms[i]);
        }
    }
    // WMS
    if (S3.gis.layers_wms) {
        for (i = 0; i < S3.gis.layers_wms.length; i++) {
            addWMSLayer(S3.gis.layers_wms[i]);
        }
    }
    // XYZ (generated server-side in s3gis.py)
    //try {
    //    addXYZLayers();
    //} catch(err) {};
    // JS (generated server-side in s3gis.py)
    try {
        addJSLayers();
    } catch(err) {};

    /* Overlays */
    // Feature Queries from Mapping API
    if (S3.gis.layers_feature_queries) {
        for (i = 0; i < S3.gis.layers_feature_queries.length; i++) {
            addGeoJSONLayer(S3.gis.layers_feature_queries[i]);
        }
    }
    // Feature Layers from Catalogue
    if (S3.gis.layers_features) {
        for (i = 0; i < S3.gis.layers_features.length; i++) {
            addGeoJSONLayer(S3.gis.layers_features[i]);
        }
    }
    // GeoJSON
    if (S3.gis.layers_geojson) {
        for (i = 0; i < S3.gis.layers_geojson.length; i++) {
            addGeoJSONLayer(S3.gis.layers_geojson[i]);
        }
    }
    // GeoRSS
    if (S3.gis.layers_georss) {
        for (i = 0; i < S3.gis.layers_georss.length; i++) {
            addGeoJSONLayer(S3.gis.layers_georss[i]);
        }
    }
    // GPX
    if (S3.gis.layers_gpx) {
        for (i = 0; i < S3.gis.layers_gpx.length; i++) {
            addGPXLayer(S3.gis.layers_gpx[i]);
        }
    }
    // KML
    if (S3.gis.layers_kml) {
        S3.gis.format_kml = new OpenLayers.Format.KML({
            extractStyles: true,
            extractAttributes: true,
            maxDepth: 2
        })
        for (i = 0; i < S3.gis.layers_kml.length; i++) {
            addKMLLayer(S3.gis.layers_kml[i]);
        }
    }
    // WFS
    if (S3.gis.layers_wfs) {
        for (i = 0; i < S3.gis.layers_wfs.length; i++) {
            addWFSLayer(S3.gis.layers_wfs[i]);
        }
    }
    // CoordinateGrid
    if (S3.gis.CoordinateGrid) {
        addCoordinateGrid();
    }
    // Draft Layers
    if (S3.gis.features || S3.gis.draw_feature || S3.gis.draw_polygon || navigator.geolocation) {
        addDraftLayer();
    }
    // Simple Features
    if (S3.gis.features) {
        for (i = 0; i < S3.gis.features.length; i++) {
            var point = new OpenLayers.Geometry.Point(S3.gis.features[i].lon, S3.gis.features[i].lat);
            point.transform(S3.gis.proj4326, S3.gis.projection_current);
            S3.gis.draftLayer.addFeatures(
                new OpenLayers.Feature.Vector(point)
            );
        }
    }
}

// Bing
function addBingLayers() {
    var bing = S3.gis.Bing;
    var ApiKey = bing.ApiKey;
    var layer;
    if (bing.Aerial) {
        layer = new OpenLayers.Layer.Bing({
            key: ApiKey,
            type: 'Aerial',
            name: bing.Aerial
        });
        map.addLayer(layer);
    }
    if (bing.Road) {
        layer = new OpenLayers.Layer.Bing({
            key: ApiKey,
            type: 'Road',
            name: bing.Road
        });
        map.addLayer(layer);
    }
    if (bing.Hybrid) {
        layer = new OpenLayers.Layer.Bing({
            key: ApiKey,
            type: 'AerialWithLabels',
            name: bing.Hybrid
        });
        map.addLayer(layer);
    }
    //if (bing.Terrain) {
    //    layer = new OpenLayers.Layer.VirtualEarth({
    //        bing.Terrain, {
    //            type: VEMapStyle.Shaded,
    //            'sphericalMercator': true
    //        }
    //    });
    //    map.addLayer(layer);
    //}
}

// CoordinateGrid
function addCoordinateGrid() {
    map.addLayer(new OpenLayers.Layer.cdauth.CoordinateGrid(null, {
        name: S3.gis.CoordinateGrid.name,
        shortName: 'grid',
        visibility: S3.gis.CoordinateGrid.visibility
    }));
}

// DraftLayer
// Used for drawing Points/Polygons & for HTML5 GeoLocation
function addDraftLayer() {
    var iconURL = S3.gis.marker_url + S3.gis.marker_default;
    var marker_height = S3.gis.marker_default_height;
    var marker_width = S3.gis.marker_default_width;
    // Needs to be uniquely instantiated
    var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
    style_marker.graphicOpacity = 1;
    style_marker.graphicWidth = marker_width;
    style_marker.graphicHeight = marker_height;
    style_marker.graphicXOffset = -(marker_width / 2);
    style_marker.graphicYOffset = -marker_height;
    style_marker.externalGraphic = iconURL;
    S3.gis.draftLayer = new OpenLayers.Layer.Vector(
        S3.i18n.gis_draft_layer, {
            style: style_marker,
            displayInLayerSwitcher: false
        }
    );
    S3.gis.draftLayer.setVisibility(true);
    map.addLayer(S3.gis.draftLayer);
}

// GeoJSON
// Used also by internal Feature Layers, Feature Queries & GeoRSS feeds
function addGeoJSONLayer(layer) {
    var name = layer.name;
    var url = layer.url;
    if (undefined != layer.marker_image) {
        // per-Layer Marker
        var marker_url = S3.gis.marker_url + layer.marker_image;
        var marker_height = layer.marker_height;
        var marker_width = layer.marker_width;
    } else {
        // per-Feature Marker or Shape
        var marker_url = '';
    }
    if (undefined != layer.refresh) {
        var refresh = layer.refresh;
    } else {
        var refresh = 900; // seconds (so 15 mins)
    }
    if (undefined != layer.dir) {
        var dir = layer.dir;
        if ( $.inArray(dir, S3.gis.dirs) == -1 ) {
            // Add this folder to the list of folders
            S3.gis.dirs.push(dir);
        }
    } else {
        // Default folder
        var dir = '';
    }
    if (undefined != layer.visibility) {
        var visibility = layer.visibility;
    } else {
        // Default to visible
        var visibility = true;
    }
    if (undefined != layer.opacity) {
        var opacity = layer.opacity;
    } else {
        // Default to opaque
        var opacity = 1;
    }
    if (undefined != layer.cluster_distance) {
        var cluster_distance = layer.cluster_distance;
    } else {
        // Default to global settings
        var cluster_distance = S3.gis.cluster_distance;
    }
    if (undefined != layer.cluster_threshold) {
        var cluster_threshold = layer.cluster_threshold;
    } else {
        // Default to global settings
        var cluster_threshold = S3.gis.cluster_threshold;
    }
    if (undefined != layer.projection) {
        var projection = layer.projection;
    } else {
        // Feature Layers, GeoRSS & KML are always in 4326
        var projection = 4326;
    }
    if (4326 == projection) {
        projection = S3.gis.proj4326;
    } else {
        projection = new OpenLayers.Projection('EPSG:' + projection);
    }

    // Style Rule For Clusters
    var cluster_style = {
        label: '${label}',
        labelAlign: 'cm',
        pointRadius: '${radius}',
        fillColor: '${fill}',
        fillOpacity: opacity,
        strokeColor: '${stroke}',
        strokeWidth: 2,
        strokeOpacity: opacity,
        graphicWidth: '${graphicWidth}',
        graphicHeight: '${graphicHeight}',
        graphicXOffset: '${graphicXOffset}',
        graphicYOffset: '${graphicYOffset}',
        graphicOpacity: opacity,
        graphicName: '${graphicName}',
        externalGraphic: '${externalGraphic}'
    };
    var cluster_options = {
        context: {
            graphicWidth: function(feature) {
                if (feature.cluster) {
                    // Clustered Point
                    var pix = '';
                } else if (feature.attributes.marker_width) {
                    // Use marker_width from feature
                    var pix = feature.attributes.marker_width;
                } else {
                    // per-Layer Marker for Unclustered Point
                    var pix = marker_width;
                }
                return pix;
            },
            graphicHeight: function(feature) {
                if (feature.cluster) {
                    // Clustered Point
                    var pix = '';
                } else if (feature.attributes.marker_height) {
                    // Use marker_height from feature
                    var pix = feature.attributes.marker_height;
                } else {
                    // per-Layer Marker for Unclustered Point
                    var pix = marker_height;
                }
                return pix;
            },
            graphicXOffset: function(feature) {
                if (feature.cluster) {
                    // Clustered Point
                    var pix = '';
                } else if (feature.attributes.marker_width) {
                    // Use marker_width from feature
                    var pix = -(feature.attributes.marker_width / 2);
                } else {
                    // per-Layer Marker for Unclustered Point
                    var pix = -(marker_width / 2);
                }
                return pix;
            },
            graphicYOffset: function(feature) {
                if (feature.cluster) {
                    // Clustered Point
                    var pix = '';
                } else if (feature.attributes.marker_height) {
                    // Use marker_height from feature
                    var pix = -feature.attributes.marker_height;
                } else {
                    // per-Layer Marker for Unclustered Point
                    var pix = -marker_height;
                }
                return pix;
            },
            //graphicOpacity: function(feature) {
                // Unclustered Point
            //    var opacity = styleMarker.opacity;
                // Clustered Point
            //    if (feature.cluster) {
            //        opacity = '';
            //    }
            //    return opacity;
            //},
            graphicName: function(feature) {
                if (feature.cluster) {
                    // Clustered Point
                    var shape = 'circle';
                } else if (feature.attributes.shape) {
                    // Use shape from feature
                    var shape = feature.attributes.shape;
                } else {
                    // default to a Circle
                    var shape = 'circle';
                }
                return shape;
            },
            externalGraphic: function(feature) {
                if (feature.cluster) {
                    // Clustered Point
                    var url = '';
                } else if (feature.attributes.marker_url) {
                    // Use marker from feature
                    var url = feature.attributes.marker_url;
                } else {
                    // per-Layer Marker for Unclustered Point
                    var url = marker_url;
                }
                return url;
            },
            radius: function(feature) {
                if (feature.cluster) {
                    // Size for Clustered Point
                    var pix = Math.min(feature.attributes.count/2, 8) + 10;
                } else if (feature.attributes.size) {
                    // Use size from feature
                    var pix = feature.attributes.size;
                } else {
                    // default Size for Unclustered Point
                    var pix = 10;
                }
                return pix;
            },
            fill: function(feature) {
                if (feature.cluster) {
                    // fillColor for Clustered Point
                    var color = '#8087ff';
                } else if (feature.attributes.colour) {
                    // Use colour from feature
                    var color = feature.attributes.colour;
                } else {
                    // default fillColor for Unclustered Point
                    var color = '#f5902e';
                }
                return color;
            },
            stroke: function(feature) {
                // strokeColor for Clustered Point
                if (feature.cluster) {
                    var color = '#2b2f76';
                } else if (feature.attributes.colour) {
                    // Use colour from feature
                    var color = feature.attributes.colour;
                } else {
                    // default strokeColor for Unclustered Point
                    var color = '#f5902e';
                }
                return color;
            },
            label: function(feature) {
                // Label For Unclustered Point
                var label = '';
                // Label For Clustered Point
                if (feature.cluster && feature.attributes.count > 1) {
                    label = feature.attributes.count;
                }
                return label;
            }
        }
    };
    // Needs to be uniquely instantiated
    var style_cluster = new OpenLayers.Style(
        cluster_style,
        cluster_options
    );
    // Define StyleMap, Using 'style_cluster' rule for 'default' styling intent
    var featureClusterStyleMap = new OpenLayers.StyleMap({
        'default': style_cluster,
        'select': {
            fillColor: '#ffdc33',
            strokeColor: '#ff9933'
        }
    });
    var geojsonLayer = new OpenLayers.Layer.Vector(
        name, {
            dir: dir,
            projection: projection,
            strategies: [
                // Need to be uniquely instantiated
                new OpenLayers.Strategy.BBOX({
                    // load features for a wider area than the visible extent to reduce calls
                    ratio: 1.5
                    // don't fetch features after every resolution change
                    //resFactor: 1
                }),
                new OpenLayers.Strategy.Refresh({
                    force: true,
                    interval: refresh * 1000 // milliseconds
                    // Close any open Popups to prevent them getting orphaned
                    // - annoying to have this happen automatically, so we handle it in onPopupClose() instead
                    //refresh: function() {
                    //    if (this.layer && this.layer.refresh) {
                    //        while (this.layer.map.popups.length) {
                    //            this.layer.map.removePopup(this.layer.map.popups[0]);
                    //        }
                    //    this.layer.refresh({force: this.force});
                    //    }
                    //}
                }),
                new OpenLayers.Strategy.Cluster({
                    distance: cluster_distance,
                    threshold: cluster_threshold
                })
            ],
            styleMap: featureClusterStyleMap,
            protocol: new OpenLayers.Protocol.HTTP({
                url: url,
                format: S3.gis.format_geojson
            })
        }
    );
    geojsonLayer.setVisibility(visibility);
    geojsonLayer.events.on({
        'featureselected': onGeojsonFeatureSelect,
        'featureunselected': onFeatureUnselect
    });
    map.addLayer(geojsonLayer);
    // Ensure Highlight & Popup Controls act on this layer
    S3.gis.layers_all.push(geojsonLayer);
}

// Google
function addGoogleLayers() {
    var google = S3.gis.Google;
    var layer;
    if (google.MapMaker || google.MapMakerHybrid) {
        if (google.Satellite) {
            layer = new OpenLayers.Layer.Google(
                google.Satellite, {
                    type: G_SATELLITE_MAP,
                    sphericalMercator: true
                }
            );
            map.addLayer(layer);
        }
        if (google.Maps) {
            layer = new OpenLayers.Layer.Google(
                google.Maps, {
                    type: G_NORMAL_MAP,
                    sphericalMercator: true
                }
            );
            map.addLayer(layer);
        }
        if (google.Hybrid) {
            layer = new OpenLayers.Layer.Google(
                google.Hybrid, {
                    type: G_HYBRID_MAP,
                    sphericalMercator: true
                }
            );
            map.addLayer(layer);
        }
        if (google.Terrain) {
            layer = new OpenLayers.Layer.Google(
                google.Terrain, {
                    type: G_PHYSICAL_MAP,
                    sphericalMercator: true
                }
            );
            map.addLayer(layer);
        }
        if (google.MapMaker) {
            layer = new OpenLayers.Layer.Google(
                google.MapMaker, {
                    type: G_MAPMAKER_NORMAL_MAP,
                    sphericalMercator: true
                }
            );
            map.addLayer(layer);
        }
        if (google.MapMakerHybrid) {
            layer = new OpenLayers.Layer.Google(
                google.MapMakerHybrid, {
                    type: G_MAPMAKER_HYBRID_MAP,
                    sphericalMercator: true
                }
            );
            map.addLayer(layer);
        }
    } else {
        if (google.Satellite) {
            layer = new OpenLayers.Layer.Google(
                google.Satellite, {
                    type: google.maps.MapTypeId.SATELLITE,
                    numZoomLevels: 22
                }
            );
            map.addLayer(layer);
        }
        if (google.Maps) {
            layer = new OpenLayers.Layer.Google(
                google.Maps, {
                    numZoomLevels: 20
                }
            );
            map.addLayer(layer);
        }
        if (google.Hybrid) {
            layer = new OpenLayers.Layer.Google(
                google.Hybrid, {
                    type: google.maps.MapTypeId.HYBRID,
                    numZoomLevels: 20
                }
            );
            map.addLayer(layer);
        }
        if (google.Terrain) {
            layer = new OpenLayers.Layer.Google(
                google.Terrain, {
                    type: google.maps.MapTypeId.TERRAIN
                }
            );
            map.addLayer(layer);
        }
    }
}

// GPX
function addGPXLayer(layer) {
    var name = layer.name;
    var url = layer.url;
    var marker_url = S3.gis.marker_url + layer.marker_image;
    var marker_height = layer.marker_height;
    var marker_width = layer.marker_width;
    if (undefined != layer.waypoints) {
        var waypoints = layer.waypoints;
    } else {
        var waypoints = true;
    }
    if (undefined != layer.tracks) {
        var tracks = layer.tracks;
    } else {
        var tracks = true;
    }
    if (undefined != layer.routes) {
        var routes = layer.routes;
    } else {
        var routes = true;
    }
    if (undefined != layer.visibility) {
        var visibility = layer.visibility;
    } else {
        var visibility = true;
    }
    if (undefined != layer.dir) {
        var dir = layer.dir;
        if ( $.inArray(dir, S3.gis.dirs) == -1 ) {
            // Add this folder to the list of folders
            S3.gis.dirs.push(dir);
        }
    } else {
        // Default folder
        var dir = '';
    }
    if (undefined != layer.opacity) {
        var opacity = layer.opacity;
    } else {
        var opacity = 1;
    }
    if (undefined != layer.cluster_distance) {
        var cluster_distance = layer.cluster_distance;
    } else {
        var cluster_distance = S3.gis.cluster_distance;
    }
    if (undefined != layer.cluster_threshold) {
        var cluster_threshold = layer.cluster_threshold;
    } else {
        var cluster_threshold = S3.gis.cluster_threshold;
    }

    // Needs to be uniquely instantiated
    var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
    if (waypoints) {
        style_marker.graphicOpacity = opacity;
        style_marker.graphicWidth = marker_width;
        style_marker.graphicHeight = marker_height;
        style_marker.graphicXOffset = -(marker_width / 2);
        style_marker.graphicYOffset = -marker_height;
        style_marker.externalGraphic = marker_url;
    } else {
        style_marker.externalGraphic = '';
    }
    style_marker.strokeColor = 'blue';
    style_marker.strokeWidth = 6;
    style_marker.strokeOpacity = opacity;

    var gpxLayer = new OpenLayers.Layer.Vector(
        name, {
            dir: dir,
            projection: S3.gis.proj4326,
            strategies: [
                // Need to be uniquely instantiated
                new OpenLayers.Strategy.Fixed(),
                new OpenLayers.Strategy.Cluster({
                    distance: cluster_distance,
                    threshold: cluster_threshold
                })
            ],
            style: style_marker,
            protocol: new OpenLayers.Protocol.HTTP({
                url: url,
                format: new OpenLayers.Format.GPX({
                    extractAttributes: true,
                    extractWaypoints: waypoints,
                    extractTracks: tracks,
                    extractRoutes: routes
                })
            })
        }
    );
    gpxLayer.setVisibility(visibility);
    gpxLayer.events.on({
        'featureselected': onGpxFeatureSelect,
        'featureunselected': onFeatureUnselect
    });
    map.addLayer(gpxLayer);
    // Ensure Highlight & Popup Controls act on this layer
    S3.gis.layers_all.push(gpxLayer);
}

// KML
function addKMLLayer(layer) {
    var name = layer.name;
    var url = layer.url;
    var marker_url = S3.gis.marker_url + layer.marker_image;
    var marker_height = layer.marker_height;
    var marker_width = layer.marker_width;
    if (undefined != layer.title) {
        var title = layer.title;
    } else {
        var title = 'name';
    }
    if (undefined != layer.body) {
        var body = layer.body;
    } else {
        var body = 'description';
    }
    if (undefined != layer.refresh) {
        var refresh = layer.refresh;
    } else {
        var refresh = 900; // seconds (so 15 mins)
    }
    if (undefined != layer.visibility) {
        var visibility = layer.visibility;
    } else {
        // Default to visible
        var visibility = true;
    }
    if (undefined != layer.dir) {
        var dir = layer.dir;
        if ( $.inArray(dir, S3.gis.dirs) == -1 ) {
            // Add this folder to the list of folders
            S3.gis.dirs.push(dir);
        }
    } else {
        // Default folder
        var dir = '';
    }
    if (undefined != layer.opacity) {
        var opacity = layer.opacity;
    } else {
        var opacity = 1;
    }
    if (undefined != layer.cluster_distance) {
        var cluster_distance = layer.cluster_distance;
    } else {
        var cluster_distance = S3.gis.cluster_distance;
    }
    if (undefined != layer.cluster_threshold) {
        var cluster_threshold = layer.cluster_threshold;
    } else {
        var cluster_threshold = S3.gis.cluster_threshold;
    }

    // Pre-cache this image
    // Need unique names, but keep scope
    S3.gis.image = new Image();
    S3.gis.image.onload = s3_gis_scaleImage;
    S3.gis.image.src = marker_url;
    // Needs to be uniquely instantiated
    var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
    style_marker.graphicOpacity = opacity;
    style_marker.graphicWidth = S3.gis.image.width;
    style_marker.graphicHeight = S3.gis.image.height;
    style_marker.graphicXOffset = -(S3.gis.image.width / 2);
    style_marker.graphicYOffset = -S3.gis.image.height;
    style_marker.externalGraphic = marker_url;
    var kmlLayer = new OpenLayers.Layer.Vector(
        name, {
            dir: dir,
            projection: S3.gis.proj4326,
            // Need to be uniquely instantiated
            strategies: [
                new OpenLayers.Strategy.Fixed(),
                new OpenLayers.Strategy.Cluster({
                    distance: cluster_distance,
                    threshold: cluster_threshold
                }),
                new OpenLayers.Strategy.Refresh({
                    force: true,
                    interval: refresh * 1000 // milliseconds
                })
            ],
            style: style_marker,
            protocol: new OpenLayers.Protocol.HTTP({
                url: url,
                format: S3.gis.format_kml
            })
        }
    );
    kmlLayer.title = title;
    kmlLayer.body = body;

    kmlLayer.setVisibility(visibility);
    kmlLayer.events.on({
        'featureselected': onKmlFeatureSelect,
        'featureunselected': onFeatureUnselect
    });
    map.addLayer(kmlLayer);
    // Ensure Highlight & Popup Controls act on this layer
    S3.gis.layers_all.push(kmlLayer);
}

// Scales the global S3.gis.image Image() object
// Used by KML Layers whose Marker is downloaded from a remote site & so we don't know the height/width in advance
var s3_gis_scaleImage = function() {
    var scaleRatio = S3.gis.image.height / S3.gis.image.width;
    var w = Math.min(S3.gis.image.width, S3.gis.max_w);
    var h = w * scaleRatio;
    if (h > S3.gis.max_h) {
        h = S3.gis.max_h;
        scaleRatio = w / h;
        w = w * scaleRatio;
    }
    S3.gis.image.height = h;
    S3.gis.image.width = w;
}

// OpenStreetMap
function addOSMLayer(layer) {
    var name = layer.name;
    var url = [layer.url1];
    if (undefined != layer.url2) {
        url.push(layer.url2);
    }
    if (undefined != layer.url3) {
        url.push(layer.url3);
    }
    if (undefined != layer.visibility) {
        var visibility = layer.visibility;
    } else {
        // Default to visible
        var visibility = true;
    }
    if (undefined != layer.dir) {
        var dir = layer.dir;
        if ( $.inArray(dir, S3.gis.dirs) == -1 ) {
            // Add this folder to the list of folders
            S3.gis.dirs.push(dir);
        }
    } else {
        // Default folder
        var dir = '';
    }
    if (undefined != layer.base) {
        var isBaseLayer = layer.base;
    } else {
        var isBaseLayer = true;
    }
    if (undefined != layer.zoomLevels) {
        var numZoomLevels = layer.zoomLevels;
    } else {
        var numZoomLevels = 19;
    }

    var osmLayer = new OpenLayers.Layer.TMS(
        name,
        url, {
            dir: dir,
            type: 'png',
            getURL: osm_getTileURL,
            displayOutsideMaxExtent: true,
            numZoomLevels: numZoomLevels,
            isBaseLayer: isBaseLayer
        }
    );
    if (undefined != layer.attribution) {
        osmLayer.attribution = layer.attribution;
    }
    osmLayer.setVisibility(visibility);
    map.addLayer(osmLayer);
}

// Supports OpenStreetMap TMS Layers
function osm_getTileURL(bounds) {
    var res = this.map.getResolution();
    var x = Math.round((bounds.left - this.maxExtent.left) / (res * this.tileSize.w));
    var y = Math.round((this.maxExtent.top - bounds.top) / (res * this.tileSize.h));
    var z = this.map.getZoom();
    var limit = Math.pow(2, z);
    if (y < 0 || y >= limit) {
        return OpenLayers.Util.getImagesLocation() + '404.png';
    } else {
        x = ((x % limit) + limit) % limit;
        var path = z + '/' + x + '/' + y + '.' + this.type;
        var url = this.url;
        if (url instanceof Array) {
            url = this.selectUrl(path, url);
        }
        return url + path;
    }
}

// TMS
function addTMSLayer(layer) {
    var name = layer.name;
    var url = [layer.url];
    if (undefined != layer.url2) {
        url.push(layer.url2);
    }
    if (undefined != layer.url3) {
        url.push(layer.url3);
    }
    var layername = layer.layername;
    if (undefined != layer.zoomLevels) {
        var numZoomLevels = layer.zoomLevels;
    } else {
        var numZoomLevels = 9;
    }
    if (undefined != layer.dir) {
        var dir = layer.dir;
        if ( $.inArray(dir, S3.gis.dirs) == -1 ) {
            // Add this folder to the list of folders
            S3.gis.dirs.push(dir);
        }
    } else {
        // Default folder
        var dir = '';
    }
    if (undefined != layer.format) {
        var format = layer.format;
    } else {
        var format = 'png';
    }

    var tmsLayer = new OpenLayers.Layer.TMS(
        name, url, {
            dir: dir,
            layername: layername,
            type: format,
            numZoomLevels: numZoomLevels
        }
    );

    if (undefined != layer.attribution) {
        tmsLayer.attribution = layer.attribution;
    }
    map.addLayer(tmsLayer);
}
// WFS
// @ToDo: WFS-T Editing: http://www.gistutor.com/openlayers/22-advanced-openlayers-tutorials/47-openlayers-wfs-t-using-a-geoserver-hosted-postgis-layer.html
function addWFSLayer(layer) {
    var name = layer.name;
    var url = layer.url;
    var title = layer.title;
    var featureType = layer.featureType;
    var featureNS = layer.featureNS;
    var schema = layer.schema;
    //var editable = layer.editable;
    if (undefined != layer.version) {
        var version = layer.version;
    } else {
        var version = '1.1.0';
    }
    if (undefined != layer.geometryName) {
        var geometryName = layer.geometryName;
    } else {
        var geometryName = 'the_geom';
    }
    if (undefined != layer.styleField) {
        var styleField = layer.styleField;
    } else {
        var styleField = '';
    }
    if (undefined != layer.styleValues) {
        var styleValues = layer.styleValues;
    } else {
        var styleValues = {};
    }
    if (undefined != layer.visibility) {
        var visibility = layer.visibility;
    } else {
        // Default to visible
        var visibility = true;
    }
    if (undefined != layer.dir) {
        var dir = layer.dir;
        if ( $.inArray(dir, S3.gis.dirs) == -1 ) {
            // Add this folder to the list of folders
            S3.gis.dirs.push(dir);
        }
    } else {
        // Default folder
        var dir = '';
    }
    if (undefined != layer.opacity) {
        var opacity = layer.opacity;
    } else {
        var opacity = 1;
    }
    if (undefined != layer.cluster_distance) {
        var cluster_distance = layer.cluster_distance;
    } else {
        var cluster_distance = S3.gis.cluster_distance;
    }
    if (undefined != layer.cluster_threshold) {
        var cluster_threshold = layer.cluster_threshold;
    } else {
        var cluster_threshold = S3.gis.cluster_threshold;
    }

    if (undefined != layer.projection) {
        var srsName = 'EPSG:' + layer.projection;
    } else {
        var srsName = 'EPSG:4326';
    }
    var protocol = new OpenLayers.Protocol.WFS({
        version: version,
        srsName: srsName,
        url: url,
        featureType: featureType,
        featureNS: featureNS,
        geometryName: geometryName,
        // Needed for WFS-T
        schema: schema
    })
    
    var cluster_options = {
        context: {
            radius: function(feature) {
                // Size for Unclustered Point
                var pix = 12;
                // Size for Clustered Point
                if (feature.cluster) {
                    pix = Math.min(feature.attributes.count/2, 8) + 12;
                }
                return pix;
            },
            fill: function(feature) {
                // fillColor for Unclustered Point
                var color = '#f5902e';
                // fillColor for Clustered Point
                if (feature.cluster) {
                    color = '#8087ff';
                }
                return color;
            },
            stroke: function(feature) {
                // strokeColor for Unclustered Point
                var color = '#f5902e';
                // strokeColor for Clustered Point
                if (feature.cluster) {
                    color = '#2b2f76';
                }
                return color;
            },
            label: function(feature) {
                // Label For Unclustered Point
                var label = '';
                // Label For Clustered Point
                if (feature.cluster && feature.attributes.count > 1) {
                    label = feature.attributes.count;
                }
                return label;
            }
        }
    }
    
    if (styleField && styleValues) {
        // Use the Custom Styling
        // Old: Make a Deep Copy of the Global Styling
        //cluster_options = $.extend(true, {}, cluster_options);
        cluster_options.context.fill = function(feature) {
            // fillColor for Unclustered Point
            var color;
            $.each( styleValues, function(i, n){
                if (i == feature.attributes[styleField]) {
                    color = n;
                }
            });
            if (!color) {
                // Default colour if we haven't had one provided
                color = '#f5902e';
            }
            // fillColor for Clustered Point
            if (feature.cluster) {
                color = '#8087ff';
            }
            return color;
        };
        cluster_options.context.stroke = function(feature) {
            // strokeColor for Unclustered Point
            var color
            $.each( styleValues, function(i, n){
                if (i == feature.attributes[styleField]) {
                    color = n;
                }
            });
            if (!color) {
                // Default colour if we haven't had one provided
                color = '#f5902e';
            }
            // strokeColor for Clustered Point
            if (feature.cluster) {
                color = '#2b2f76';
            }
            return color;
        };
    }
    
    // Needs to be uniquely instantiated
    var style_cluster = new OpenLayers.Style (
        {
            label: '${label}',
            labelAlign: 'cm',
            pointRadius: '${radius}',
            fillColor: '${fill}',
            fillOpacity: opacity / 2,
            strokeColor: '${stroke}',
            strokeWidth: 2,
            strokeOpacity: opacity
        },
        cluster_options
    );
    // Define StyleMap, Using 'style_cluster' rule for 'default' styling intent
    var featureClusterStyleMap = new OpenLayers.StyleMap({
        'default': style_cluster,
        'select': {
            fillColor: '#ffdc33',
            strokeColor: '#ff9933'
        }
    });

    if ((!projection) || ('4326' == projection)) {
        projection = S3.gis.proj4326;
    } else {
        projection = new OpenLayers.Projection('EPSG:' + projection);
    }

    // Put these in Global Scope & i18n the messages
    //function showSuccessMsg(){
    //    showMsg("Transaction successfully completed");
    //};
    //function showFailureMsg(){
    //    showMsg("An error occured while operating the transaction");
    //};
    // if Editable
    // Set up a save strategy
    //var saveStrategy = new OpenLayers.Strategy.Save();
    //saveStrategy.events.register("success", '', showSuccessMsg);
    //saveStrategy.events.register("failure", '', showFailureMsg);

    var wfsLayer = new OpenLayers.Layer.Vector(
        name, {
        // limit the number of features to avoid browser freezes
        maxFeatures: 1000,
        strategies: [
            new OpenLayers.Strategy.BBOX({
                // load features for a wider area than the visible extent to reduce calls
                ratio: 1.5
                // don't fetch features after every resolution change
                //resFactor: 1
            }),
            new OpenLayers.Strategy.Cluster({
                distance: cluster_distance,
                threshold: cluster_threshold
            })//,
            // if Editable
            //saveStrategy
        ],
        dir: dir,
        projection: projection,
        //outputFormat: "json",
        //readFormat: new OpenLayers.Format.GeoJSON(),
        protocol: protocol,
        styleMap: featureClusterStyleMap
    });

    wfsLayer.title = title;
    wfsLayer.setVisibility(visibility);
    wfsLayer.events.on({
        'featureselected': onWfsFeatureSelect,
        'featureunselected': onFeatureUnselect
    });
    map.addLayer(wfsLayer);
    // Ensure Highlight & Popup Controls act on this layer
    S3.gis.layers_all.push(wfsLayer);
}

// WMS
function addWMSLayer(layer) {
    var name = layer.name;
    var url = layer.url;
    var layers = layer.layers;
    if (undefined != layer.visibility) {
        var visibility = layer.visibility;
    } else {
        var visibility = true;
    }
    if (undefined != layer.dir) {
        var dir = layer.dir;
        if ( $.inArray(dir, S3.gis.dirs) == -1 ) {
            // Add this folder to the list of folders
            S3.gis.dirs.push(dir);
        }
    } else {
        // Default folder
        var dir = '';
    }
    if (undefined != layer.base) {
        var isBaseLayer = layer.base;
    } else {
        var isBaseLayer = false;
    }
    if (undefined != layer.transparent) {
        var transparent = layer.transparent;
    } else {
        var transparent = true;
    }
    if (undefined != layer.format) {
        var format = layer.format;
    } else {
        var format = 'image/png';
    }
    if (undefined != layer.version) {
        var version = layer.version;
    } else {
        var version = '1.1.1';
    }
    if (undefined != layer.map) {
        var wms_map = layer.map;
    } else {
        var wms_map = '';
    }
    if (undefined != layer.style) {
        var style = layer.style;
    } else {
        var style = '';
    }
    if (undefined != layer.bgcolor) {
        var bgcolor = '0x' + layer.bgcolor;
    } else {
        var bgcolor = '';
    }
    if (undefined != layer.buffer) {
        var buffer = layer.buffer;
    } else {
        var buffer = 0;
    }
    if (undefined != layer.tiled) {
        var tiled = layer.tiled;
    } else {
        var tiled = false;
    }
    if (undefined != layer.opacity) {
        var opacity = layer.opacity;
    } else {
        var opacity = 1;
    }
    if (undefined != layer.queryable) {
        var queryable = layer.queryable;
    } else {
        var queryable = 1;
    }

    var wmsLayer = new OpenLayers.Layer.WMS(
        name, url, {
            layers: layers
        },
        {
            dir: dir,
            wrapDateLine: true,
            isBaseLayer: isBaseLayer,
            queryable: queryable,
            visibility: visibility
        }
    );
    if (wms_map) {
        wmsLayer.params.MAP = wms_map;
    }
    if (format) {
        wmsLayer.params.FORMAT = format;
    }
    if (transparent) {
        wmsLayer.params.TRANSPARENT = true;
    }
    if (version) {
        wmsLayer.params.VERSION = version;
    }
    if (style) {
        wmsLayer.params.STYLES = style;
    }
    if (bgcolor) {
        wmsLayer.params.BGCOLOR = bgcolor;
    }
    if (tiled) {
        wmsLayer.params.TILED = true;
        wmsLayer.params.TILESORIGIN = [map.maxExtent.left, map.maxExtent.bottom];
    }
    if (!isBaseLayer) {
        wmsLayer.opacity = opacity;
        if (buffer) {
            wmsLayer.buffer = buffer;
        } else {
            wmsLayer.buffer = 0;
        }
    }
    map.addLayer(wmsLayer);
}

// Support GeoJSON Layers
// including those from internal Features, Feature Queries & cached GeoRSS feeds
function s3_gis_loadDetails(url, id, popup) {
    // Load the Popup Details asynchronously
    $.ajax({
        'url': url,
        'success': function(data) {
            $('#' + id).html(data);
            popup.updateSize();
        },
        'error': function(request, status, error) {
            if (error == 'UNAUTHORIZED') {
                msg = S3.i18n.gis_requires_login;
            } else {
                msg = request.responseText;
            }
            $('#' + id + '_contentDiv').html(msg);
            popup.updateSize();
        },
        'dataType': 'html'
    });
}
function onGeojsonFeatureSelect(event) {
    // unselect any previous selections
    s3_gis_tooltipUnselect(event);
    var feature = event.feature;
    //S3.gis.selectedFeature = feature;
    var popup_id = S3.uid();
    var centerPoint = feature.geometry.getBounds().getCenterLonLat();
    var data_link = false;
    if (feature.cluster) {
        // Cluster
        var name, uuid, url;
        var contents = S3.i18n.gis_cluster_multiple + ':<ul>';
        for (var i = 0; i < feature.cluster.length; i++) {
            if (undefined != feature.cluster[i].attributes.popup) {
                // Only display the 1st line of the hover popup
                name = feature.cluster[i].attributes.popup.split('<br />', 1)[0]; 
            } else {
                name = feature.cluster[i].attributes.name;
            }
            if (undefined != feature.cluster[i].attributes.url) {
                url = feature.cluster[i].attributes.url;
                contents += "<li><a href='javascript:s3_gis_loadClusterPopup(" + "\"" + url + "\", \"" + popup_id + "\"" + ")'>" + name + "</a></li>";
            } else {
                // @ToDo: Provide a way to load non-URL based popups
                contents += '<li>' + name + '</li>';
            }
        }
        contents += '</ul>';
        contents += "<div align='center'><a href='javascript:s3_gis_zoomToSelectedFeature(" + centerPoint.lon + "," + centerPoint.lat + ", 3)'>Zoom in</a></div>";
    } else {
        // Single Feature
        if (undefined != feature.attributes.url) {
            // Popup contents are pulled via AJAX
            var contents = S3.i18n.gis_loading + "...<img src='" + S3.gis.ajax_loader + "' border=0 />";
        } else {
            // Popup contents are built from the attributes
            if (undefined == feature.attributes.name) {
                var name = '';
            } else {
                var name = '<h3>' + feature.attributes.name + '</h3>';
            };
            if (undefined == feature.attributes.description) {
                var description = '';
            } else {
                var description = '<p>' + feature.attributes.description + '</p>';
            };
            if (undefined == feature.attributes.link) {
                var link = '';
            } else {
                var link = '<a href="' + feature.attributes.link + '" target="_blank">' + feature.attributes.link + '</a>';
            };
            if (undefined == feature.attributes.data) {
                var data = '';
            } else if (feature.attributes.data.indexOf('http://') === 0) {
                data_link = true;
                var data_id = S3.uid();
                var data = '<div id="' + data_id + '">' + S3.i18n.gis_loading + "...<img src='" + S3.gis.ajax_loader + "' border=0 />" + '</div>';
            } else {
                var data = '<p>' + feature.attributes.data + '</p>';
            };
            if (undefined == feature.attributes.image) {
                var image = '';
            } else if (feature.attributes.image.indexOf('http://') === 0) {
                var image = '<img src="' + feature.attributes.image + '" height=300 width=300>';
            } else {
                var image = '';
            };
            var contents = name + description + link + data + image;
        }
    };
    var popup = new OpenLayers.Popup.FramedCloud(
        popup_id,
        centerPoint,
        new OpenLayers.Size(200, 200),
        contents,
        null,
        true,
        onPopupClose
    );
    if (undefined != feature.attributes.url) {
        // call AJAX to get the contentHTML
        var popup_url = feature.attributes.url;
        s3_gis_loadDetails(popup_url, popup_id + '_contentDiv', popup);
    } else if (data_link) {
        // call AJAX to get the data
        s3_gis_loadDetails(feature.attributes.data, data_id, popup);
    }
    feature.popup = popup;
    //popup.feature = feature;
    map.addPopup(popup);
}

// Support GPX Layers
function onGpxFeatureSelect(event) {
    // unselect any previous selections
    s3_gis_tooltipUnselect(event);
    var feature = event.feature;
    // Anything we want to do here?
}

// Support KML Layers
// @ToDo: Remove once moved to GeoJSON
function onKmlFeatureSelect(event) {
    // unselect any previous selections
    s3_gis_tooltipUnselect(event);
    var feature = event.feature;
    //S3.gis.selectedFeature = feature;
    var popup_id = S3.uid();
    var centerPoint = feature.geometry.getBounds().getCenterLonLat();
    var titleField = feature.layer.title;
    var attributes = feature.attributes;
    var type = typeof attributes[titleField];
    if ('object' == type) {
        var title = attributes[titleField].value;
    } else {
        var title = attributes[titleField];
    }
    var body = feature.layer.body.split(' ');
    var content = '';
    for (var i = 0; i < body.length; i++) {
        type = typeof attributes[body[i]];
        if ('object' == type) {
            // Geocommons style
            var displayName = attributes[body[i]].displayName;
            if (displayName == '') {
                displayName = body[i];
            }
            var value = attributes[body[i]].value;
            var row = '<b>' + displayName + '</b>: ' + value + '<br />';
        } else {
            var row = attributes[body[i]] + '<br />';
        }
        content += row;
    }
    // Protect the content against JavaScript attacks
    if (content.search('<script') != -1) {
        content = 'Content contained Javascript! Escaped content below.<br />' + content.replace(/</g, '<');
    }
    var contents = '<h3>' + title + '</h3>' + content;

    var popup = new OpenLayers.Popup.FramedCloud(
        popup_id,
        centerPoint,
        new OpenLayers.Size(200, 200),
        contents,
        null,
        true,
        onPopupClose
    );
    feature.popup = popup;
    map.addPopup(popup);
}

// Support WFS Layers
// @ToDo: See if this can be DRYed
function onWfsFeatureSelect(event) {
    // unselect any previous selections
    s3_gis_tooltipUnselect(event);
    var feature = event.feature;
    //S3.gis.selectedFeature = feature;
    var popup_id = S3.uid();
    var centerPoint = feature.geometry.getBounds().getCenterLonLat();
    var titleField = feature.layer.title;
    if (feature.cluster) {
        // Cluster
        var name;
        var contents = S3.i18n.gis_cluster_multiple + ':<ul>';
        var length = Math.min(feature.cluster.length, 9);
        for (var i = 0; i < length; i++) {
            name = feature.cluster[i].attributes[titleField];
            contents += '<li>' + name + '</li>';
        }
        contents += '</ul>';
        contents += "<div align='center'><a href='javascript:s3_gis_zoomToSelectedFeature(" + centerPoint.lon + "," + centerPoint.lat + ", 3)'>Zoom in</a></div>";
    } else {
        // Single Feature
        var attributes = feature.attributes;
        var title = attributes[titleField];
        var content = '';
        $.each( attributes, function(i, n){
            content += '<b>' + i + ':</b> ' + n + '<br />';
        });
        var contents = '<h3>' + title + '</h3>' + content;
    }
    var popup = new OpenLayers.Popup.FramedCloud(
        popup_id,
        centerPoint,
        new OpenLayers.Size(200, 200),
        contents,
        null,
        true,
        onPopupClose
    );
    feature.popup = popup;
    map.addPopup(popup);
}
