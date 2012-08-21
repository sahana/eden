/**
 * S3 GIS Layers
 * Used by the Map (modules/s3gis.py)
 * For Production usage gets assembled into s3.gis.min.js
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

// Add Layers from the Catalogue
function addLayers() {
    var i;
    /* Base Layers */
    // OSM
    if (S3.gis.layers_osm) {
        for (i = S3.gis.layers_osm.length; i > 0; i--) {
            addOSMLayer(S3.gis.layers_osm[i - 1]);
        }
    }
    // Google
    try {
        // Only load Google layers if GoogleAPI downloaded ok
        // - allow rest of map to work offline
        google & addGoogleLayers();
    } catch(err) {};
    // Bing
    if (S3.gis.Bing) {
        addBingLayers();
    }
    // TMS
    if (S3.gis.layers_tms) {
        for (i = S3.gis.layers_tms.length; i > 0; i--) {
            addTMSLayer(S3.gis.layers_tms[i - 1]);
        }
    }
    // WMS
    if (S3.gis.layers_wms) {
        for (i = S3.gis.layers_wms.length; i > 0; i--) {
            addWMSLayer(S3.gis.layers_wms[i - 1]);
        }
    }
    // XYZ
    if (S3.gis.layers_xyz) {
        for (i = S3.gis.layers_xyz.length; i > 0; i--) {
            addXYZLayer(S3.gis.layers_xyz[i - 1]);
        }
    }
    // Empty
    if (S3.gis.EmptyLayer) {
        var layer = new OpenLayers.Layer(S3.gis.EmptyLayer.name, {
                isBaseLayer: true,
                displayInLayerSwitcher: true,
                // This is used to Save State
                s3_layer_id: S3.gis.EmptyLayer.id,
                s3_layer_type: 'empty'
            }
        );
        map.addLayer(layer);
        if (S3.gis.EmptyLayer.base) {
            map.setBaseLayer(layer);
        }
    }
    // JS (generated server-side in s3gis.py)
    try {
        addJSLayers();
    } catch(err) {};

    /* Overlays */
    // Theme
    if (S3.gis.layers_theme) {
        for (i = S3.gis.layers_theme.length; i > 0; i--) {
            addGeoJSONLayer(S3.gis.layers_theme[i - 1]);
        }
    }
    // GeoJSON
    if (S3.gis.layers_geojson) {
        for (i = S3.gis.layers_geojson.length; i > 0; i--) {
            addGeoJSONLayer(S3.gis.layers_geojson[i - 1]);
        }
    }
    // GPX
    if (S3.gis.layers_gpx) {
        for (i = S3.gis.layers_gpx.length; i > 0; i--) {
            addGPXLayer(S3.gis.layers_gpx[i - 1]);
        }
    }
    // ArcGIS REST
    if (S3.gis.layers_arcrest) {
        for (i = S3.gis.layers_arcrest.length; i > 0; i--) {
            addArcRESTLayer(S3.gis.layers_arcrest[i - 1]);
        }
    }
    // CoordinateGrid
    if (S3.gis.CoordinateGrid) {
        addCoordinateGrid();
    }
    // GeoRSS
    if (S3.gis.layers_georss) {
        for (i = S3.gis.layers_georss.length; i > 0; i--) {
            addGeoJSONLayer(S3.gis.layers_georss[i - 1]);
        }
    }
    // KML
    if (S3.gis.layers_kml) {
        S3.gis.format_kml = new OpenLayers.Format.KML({
            extractStyles: true,
            extractAttributes: true,
            maxDepth: 2
        })
        for (i = S3.gis.layers_kml.length; i > 0; i--) {
            addKMLLayer(S3.gis.layers_kml[i - 1]);
        }
    }
    // OpenWeatherMap
    if (S3.gis.OWM) {
        addOWMLayers();
    }
    // WFS
    if (S3.gis.layers_wfs) {
        for (i = S3.gis.layers_wfs.length; i > 0; i--) {
            addWFSLayer(S3.gis.layers_wfs[i - 1]);
        }
    }
    // Feature Queries from Mapping API
    if (S3.gis.layers_feature_queries) {
        for (i = S3.gis.layers_feature_queries.length; i > 0; i--) {
            addGeoJSONLayer(S3.gis.layers_feature_queries[i - 1]);
        }
    }
    // Feature Resources (e.g. Search Results))
    if (S3.gis.layers_feature_resources) {
        for (i = S3.gis.layers_feature_resources.length; i > 0; i--) {
            addGeoJSONLayer(S3.gis.layers_feature_resources[i - 1]);
        }
    }
    // Feature Layers from Catalogue
    if (S3.gis.layers_features) {
        for (i = S3.gis.layers_features.length; i > 0; i--) {
            addGeoJSONLayer(S3.gis.layers_features[i - 1]);
        }
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

// ArcGIS REST
/*
@ToDo: Features not Images, so that we can have popups
- will require a new OpenLayers.Format.ArcREST

@ToDo: Support Token Authentication
- Request Token during init of layer:
result = GET http[s]://hostname/ArcGIS/tokens?request=getToken&username=myusername&password=mypassword
- Append ?token=result to the URL
*/
function addArcRESTLayer(layer) {
    var name = layer.name;
    var url = [layer.url];
    if (undefined != layer.layers) {
        var layers = layer.layers;
    } else {
        // Default layer
        var layers = 0;
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
    if (undefined != layer.visibility) {
        var visibility = layer.visibility;
    } else {
        // Default to visible
        var visibility = true;
    }

    var arcRESTLayer = new OpenLayers.Layer.ArcGIS93Rest(
        name, url, {
            // There are other possible options, but this should be sufficient for our needs
            layers: 'show:' + layers,
            isBaseLayer: isBaseLayer,
            transparent: transparent,
            dir: dir,
            // This is used to Save State
            s3_layer_id: layer.id,
            s3_layer_type: 'arcrest'
        }
    );

    arcRESTLayer.setVisibility(visibility);

    map.addLayer(arcRESTLayer);
    if (layer._base) {
        map.setBaseLayer(arcRESTLayer);
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
            name: bing.Aerial.name,
            // This is used to Save State
            s3_layer_id: bing.Aerial.id,
            s3_layer_type: 'bing'
        });
        map.addLayer(layer);
        if (bing.Base == 'aerial') {
            map.setBaseLayer(layer);
        }
    }
    if (bing.Road) {
        layer = new OpenLayers.Layer.Bing({
            key: ApiKey,
            type: 'Road',
            name: bing.Road.name,
            // This is used to Save State
            s3_layer_id: bing.Road.id,
            s3_layer_type: 'bing'
        });
        map.addLayer(layer);
        if (bing.Base == 'road') {
            map.setBaseLayer(layer);
        }
    }
    if (bing.Hybrid) {
        layer = new OpenLayers.Layer.Bing({
            key: ApiKey,
            type: 'AerialWithLabels',
            name: bing.Hybrid.name,
            // This is used to Save State
            s3_layer_id: bing.Hybrid.id,
            s3_layer_type: 'bing'
        });
        map.addLayer(layer);
        if (bing.Base == 'hybrid') {
            map.setBaseLayer(layer);
        }
    }
}

// CoordinateGrid
function addCoordinateGrid() {
    map.addLayer(new OpenLayers.Layer.cdauth.CoordinateGrid(null, {
        name: S3.gis.CoordinateGrid.name,
        shortName: 'grid',
        visibility: S3.gis.CoordinateGrid.visibility,
        // This is used to Save State
        s3_layer_id: S3.gis.CoordinateGrid.id,
        s3_layer_type: 'coordinate'
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

/**
 * Class: OpenLayers.Strategy.AttributeCluster
 * Strategy for vector feature clustering based on feature attributes.
 *
 * Inherits from:
 *  - <OpenLayers.Strategy.Cluster>
 */
OpenLayers.Strategy.AttributeCluster = OpenLayers.Class(OpenLayers.Strategy.Cluster, {
    /**
     * the attribute to use for comparison
     */
    attribute: null,
    /**
     * Method: shouldCluster
     * Determine whether to include a feature in a given cluster.
     *
     * Parameters:
     * cluster - {<OpenLayers.Feature.Vector>} A cluster.
     * feature - {<OpenLayers.Feature.Vector>} A feature.
     *
     * Returns:
     * {Boolean} The feature should be included in the cluster.
     */
    shouldCluster: function(cluster, feature) {
        var cc_attrval = cluster.cluster[0].attributes[this.attribute];
        var fc_attrval = feature.attributes[this.attribute];
        var superProto = OpenLayers.Strategy.Cluster.prototype;
        return cc_attrval === fc_attrval && 
               superProto.shouldCluster.apply(this, arguments);
    },
    CLASS_NAME: "OpenLayers.Strategy.AttributeCluster"
});

// GeoJSON
// Used also by internal Feature Layers, Feature Queries, Feature Resources
// & GeoRSS feeds
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
    if (undefined != layer.type) {
        var layer_type = layer.type;
    } else {
        // Feature Layers
        var layer_type = 'feature';
    }
    if (undefined != layer.style) {
        var style = layer.style;
    } else {
        var style = [];
    }

    // Style Rule For Clusters
    var cluster_style = {
        label: '${label}',
        labelAlign: 'cm',
        pointRadius: '${radius}',
        fillColor: '${fill}',
        fillOpacity: '${fillOpacity}',
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
                    if (feature.cluster[0].attributes.colour) {
                        // Use colour from features
                        var color = feature.cluster[0].attributes.colour;
                    } else {
                        // default fillColor for Clustered Point
                        var color = '#8087ff';
                    }
                } else if (feature.attributes.colour) {
                    // Feature Query: Use colour from feature
                    var color = feature.attributes.colour;
                } else if (style.length) {
                    // Theme Layer: Lookup colour from style rule
                    var value = feature.attributes.value;
                    var color;
                    $.each(style, function(index, elem) { 
                        if ((value >= elem.low) && (value < elem.high)) {
                            color = elem.fill;
                            return false;
                        }
                    });
                    if (undefined != color) {
                        color = '#' + color;
                    } else {
                        // default fillColor
                        color = '#000000';
                    }
                } else {
                    // default fillColor for Unclustered Point
                    var color = '#f5902e';
                }
                return color;
            },
            fillOpacity: function(feature) {
                if (feature.cluster) {
                    if (feature.cluster[0].attributes.opacity) {
                        // Use opacity from features
                        var opacity = feature.cluster[0].attributes.opacity;
                    } else {
                        // default fillOpacity for Clustered Point
                        var opacity = opacity;
                    }
                } else if (feature.attributes.opacity) {
                    // Use opacity from feature
                    var opacity = feature.attributes.opacity;
                } else {
                    // default fillOpacity for Unclustered Point
                    var opacity = opacity;
                }
                return opacity;
            },
            stroke: function(feature) {
                if (feature.cluster) {
                    if (feature.cluster[0].attributes.colour) {
                        // Use colour from features
                        var color = feature.cluster[0].attributes.colour;
                    } else {
                        // default strokeColor for Clustered Point
                        var color = '#2b2f76';
                    }
                } else if (feature.attributes.colour) {
                    // Feature Query: Use colour from feature
                    var color = feature.attributes.colour;
                } else if (style.length) {
                    // Theme Layer: Lookup colour from style rule
                    var value = feature.attributes.value;
                    var color;
                    $.each(style, function(index, elem) { 
                        if ((value >= elem.low) && (value < elem.high)) {
                            color = elem.fill;
                            return false;
                        }
                    });
                    if (undefined != color) {
                        color = '#' + color;
                    } else {
                        // default fillColor
                        color = '#000000';
                    }
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
    if (style.length) {
        var rules = [];
        var fill;
        $.each(style, function(index, elem) {
            fill = '#' + elem.fill;
            var rule = new OpenLayers.Rule({
                filter: new OpenLayers.Filter.Comparison({
                    type: OpenLayers.Filter.Comparison.BETWEEN,
                    property: 'value',
                    lowerBoundary: elem.low,
                    upperBoundary: elem.high
                }),
                symbolizer: {
                    fillColor: fill,
                    strokeColor: fill,
                    // @ToDo: Have the Legend to use a Square but the actual features to use a circle
                    graphicName: 'circle',
                    pointRadius: 10
                },
                title: elem.low + '-' + elem.high
            });
            rules.push(rule);
        });
        style_cluster.addRules(rules);
    }
    // Define StyleMap, Using 'style_cluster' rule for 'default' styling intent
    var featureClusterStyleMap = new OpenLayers.StyleMap({
        'default': style_cluster,
        // @ToDo: Customise the Select Style too
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
                new OpenLayers.Strategy.AttributeCluster({
                    attribute: 'colour',
                    distance: cluster_distance,
                    threshold: cluster_threshold
                })
            ],
            // This gets picked up after mapPanel instantiates & copied to it's layerRecords
            legendURL: marker_url,
            // These is used to Save State & locate Layer to Activate/Refresh
            s3_layer_id: layer.id,
            s3_layer_type: layer_type,
            s3_style: style,
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
        'featureunselected': onFeatureUnselect,
        'loadstart': showThrobber,
        'loadend': hideThrobber,
        'loadcancel': hideThrobber
    });
    map.addLayer(geojsonLayer);
    // Ensure Highlight & Popup Controls act on this layer
    S3.gis.layers_all.push(geojsonLayer);
    // Ensure marker layers are rendered over other layers
    //map.setLayerIndex(geojsonLayer, 99);
}

// Google
function addGoogleLayers() {
    var google = S3.gis.Google;
    var layer;
    if (google.MapMaker || google.MapMakerHybrid) {
        // v2 API
        if (google.Satellite) {
            layer = new OpenLayers.Layer.Google(
                google.Satellite.name, {
                    type: G_SATELLITE_MAP,
                    sphericalMercator: true,
                    // This is used to Save State
                    s3_layer_id: google.Satellite.id,
                    s3_layer_type: 'google'
                }
            );
            map.addLayer(layer);
            if (google.Base == 'satellite') {
                map.setBaseLayer(layer);
            }
        }
        if (google.Maps) {
            layer = new OpenLayers.Layer.Google(
                google.Maps.name, {
                    type: G_NORMAL_MAP,
                    sphericalMercator: true,
                    // This is used to Save State
                    s3_layer_id: google.Maps.id,
                    s3_layer_type: 'google'
                }
            );
            map.addLayer(layer);
            if (google.Base == 'maps') {
                map.setBaseLayer(layer);
            }
        }
        if (google.Hybrid) {
            layer = new OpenLayers.Layer.Google(
                google.Hybrid.name, {
                    type: G_HYBRID_MAP,
                    sphericalMercator: true,
                    // This is used to Save State
                    s3_layer_id: google.Hybrid.id,
                    s3_layer_type: 'google'
                }
            );
            map.addLayer(layer);
            if (google.Base == 'maps') {
                map.setBaseLayer(layer);
            }
        }
        if (google.Terrain) {
            layer = new OpenLayers.Layer.Google(
                google.Terrain.name, {
                    type: G_PHYSICAL_MAP,
                    sphericalMercator: true,
                    // This is used to Save State
                    s3_layer_id: google.Terrain.id,
                    s3_layer_type: 'google'
                }
            );
            map.addLayer(layer);
            if (google.Base == 'terrain') {
                map.setBaseLayer(layer);
            }
        }
        if (google.MapMaker) {
            layer = new OpenLayers.Layer.Google(
                google.MapMaker.name, {
                    type: G_MAPMAKER_NORMAL_MAP,
                    sphericalMercator: true,
                    // This is used to Save State
                    s3_layer_id: layer.id,
                    s3_layer_type: 'google'
                }
            );
            map.addLayer(layer);
            if (google.Base == 'mapmaker') {
                map.setBaseLayer(layer);
            }
        }
        if (google.MapMakerHybrid) {
            layer = new OpenLayers.Layer.Google(
                google.MapMakerHybrid.name, {
                    type: G_MAPMAKER_HYBRID_MAP,
                    sphericalMercator: true,
                    // This is used to Save State
                    s3_layer_id: layer.id,
                    s3_layer_type: 'google'
                }
            );
            map.addLayer(layer);
            if (google.Base == 'mapmakerhybrid') {
                map.setBaseLayer(layer);
            }
        }
    } else {
        // v3 API
        if (google.Satellite) {
            layer = new OpenLayers.Layer.Google(
                google.Satellite.name, {
                    type: 'satellite',
                    numZoomLevels: 22,
                    // This is used to Save State
                    s3_layer_id: google.Satellite.id,
                    s3_layer_type: 'google'
                }
            );
            map.addLayer(layer);
            if (google.Base == 'satellite') {
                map.setBaseLayer(layer);
            }
        }
        if (google.Maps) {
            layer = new OpenLayers.Layer.Google(
                google.Maps.name, {
                    numZoomLevels: 20,
                    // This is used to Save State
                    s3_layer_id: google.Maps.id,
                    s3_layer_type: 'google'
                }
            );
            map.addLayer(layer);
            if (google.Base == 'maps') {
                map.setBaseLayer(layer);
            }
        }
        if (google.Hybrid) {
            layer = new OpenLayers.Layer.Google(
                google.Hybrid.name, {
                    type: 'hybrid',
                    numZoomLevels: 20,
                    // This is used to Save State
                    s3_layer_id: google.Hybrid.id,
                    s3_layer_type: 'google'
                }
            );
            map.addLayer(layer);
            if (google.Base == 'hybrid') {
                map.setBaseLayer(layer);
            }
        }
        if (google.Terrain) {
            layer = new OpenLayers.Layer.Google(
                google.Terrain.name, {
                    type: 'terrain',
                    // This is used to Save State
                    s3_layer_id: google.Terrain.id,
                    s3_layer_type: 'google'
                }
            );
            map.addLayer(layer);
            if (google.Base == 'terrain') {
                map.setBaseLayer(layer);
            }
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
            // This is used to Save State
            s3_layer_id: layer.id,
            s3_layer_type: 'gpx',
            // This gets picked up after mapPanel instantiates & copied to it's layerRecords
            legendURL: marker_url,
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
        'featureunselected': onFeatureUnselect,
        'loadstart': showThrobber,
        'loadend': hideThrobber,
        'loadcancel': hideThrobber
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
    // - don't we need an array of these!?
    S3.gis.image = new Image();
    S3.gis.image.onload = s3_gis_scaleImage;
    S3.gis.image.src = marker_url;
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
        graphicName: 'circle',
        externalGraphic: '${externalGraphic}'
    };
    var cluster_options = {
        context: {
            graphicWidth: function(feature) {
                if (feature.cluster) {
                    // Clustered Point
                    var pix = '';
                } else {
                    var pix = S3.gis.image.width;
                }
                return pix;
            },
            graphicHeight: function(feature) {
                if (feature.cluster) {
                    // Clustered Point
                    var pix = '';
                } else {
                    var pix = S3.gis.image.height;
                }
                return pix;
            },
            graphicXOffset: function(feature) {
                if (feature.cluster) {
                    // Clustered Point
                    var pix = '';
                } else {
                    var pix = -(S3.gis.image.width / 2);
                }
                return pix;
            },
            graphicYOffset: function(feature) {
                if (feature.cluster) {
                    // Clustered Point
                    var pix = '';
                } else {
                    var pix = -S3.gis.image.height;
                }
                return pix;
            },
            externalGraphic: function(feature) {
                if (feature.cluster) {
                    // Clustered Point
                    var url = '';
                } else {
                    var url = marker_url;
                }
                return url;
            },
            radius: function(feature) {
                if (feature.cluster) {
                    // Size for Clustered Point
                    var pix = Math.min(feature.attributes.count/2, 8) + 10;
                } else {
                    // default Size for Unclustered Point
                    var pix = 10;
                }
                return pix;
            },
            fill: function(feature) {
                if (feature.cluster) {
                    // default fillColor for Clustered Point
                    var color = '#8087ff';
                } else {
                    // default fillColor for Unclustered Point
                    var color = '#f5902e';
                }
                return color;
            },
            stroke: function(feature) {
                if (feature.cluster) {
                    // default strokeColor for Clustered Point
                    var color = '#2b2f76';
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
        // @ToDo: Customise the Select Style too
        'select': {
            fillColor: '#ffdc33',
            strokeColor: '#ff9933'
        }
    });
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
            // This is used to Save State
            s3_layer_id: layer.id,
            s3_layer_type: 'kml',
            // This gets picked up after mapPanel instantiates & copied to it's layerRecords
            legendURL: marker_url,
            styleMap: featureClusterStyleMap,
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
        'featureunselected': onFeatureUnselect,
        'loadstart': showThrobber,
        'loadend': hideThrobber,
        'loadcancel': hideThrobber
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
            isBaseLayer: isBaseLayer,
            // This is used to Save State
            s3_layer_id: layer.id,
            s3_layer_type: 'openstreetmap'
        }
    );
    if (undefined != layer.attribution) {
        osmLayer.attribution = layer.attribution;
    }
    osmLayer.setVisibility(visibility);
    map.addLayer(osmLayer);
    if (layer._base) {
        map.setBaseLayer(osmLayer);
    }
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

// OpenWeatherMap
function addOWMLayers() {
    var owm = S3.gis.OWM;
    var layer;
    if (owm.station) {
        layer = new OpenLayers.Layer.Vector.OWMStations(
            owm.station.name,
            {dir: owm.station.dir,
             // This is used to Save State
             s3_layer_id: owm.station.id,
             s3_layer_type: 'openweathermap'
            }
        );
        layer.setVisibility(owm.city.visibility);
        layer.events.on({
            'featureselected': layer.onSelect,
            'featureunselected': layer.onUnselect,
            'loadstart': showThrobber,
            'loadend': hideThrobber,
            'loadcancel': hideThrobber
        });
        map.addLayer(layer);
        // Ensure Highlight & Popup Controls act on this layer
        S3.gis.layers_all.push(layer);
    }
    if (owm.city) {
        layer = new OpenLayers.Layer.Vector.OWMWeather(
            owm.city.name,
            {dir: owm.station.dir,
             // This is used to Save State
             s3_layer_id: owm.city.id,
             s3_layer_type: 'openweathermap'
            }
        );
        layer.setVisibility(owm.city.visibility);
        layer.events.on({
            'featureselected': layer.onSelect,
            'featureunselected': layer.onUnselect,
            'loadstart': showThrobber,
            'loadend': hideThrobber,
            'loadcancel': hideThrobber
        });
        map.addLayer(layer);
        // Ensure Highlight & Popup Controls act on this layer
        S3.gis.layers_all.push(layer);
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
        var numZoomLevels = 19;
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
            // This is used to Save State
            s3_layer_id: layer.id,
            s3_layer_type: 'tms',
            layername: layername,
            type: format,
            numZoomLevels: numZoomLevels
        }
    );

    if (undefined != layer.attribution) {
        tmsLayer.attribution = layer.attribution;
    }
    map.addLayer(tmsLayer);
    if (layer._base) {
        map.setBaseLayer(tmsLayer);
    }
}

// WFS
// @ToDo: WFS-T Editing: http://www.gistutor.com/openlayers/22-advanced-openlayers-tutorials/47-openlayers-wfs-t-using-a-geoserver-hosted-postgis-layer.html
function addWFSLayer(layer) {
    var name = layer.name;
    var url = layer.url;
    if ((undefined != layer.username) && (undefined != layer.password)) {
        var username = layer.username;
        var password = layer.password;
        url = url.replace('://', '://' + username + ':' + password + '@');
    }
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
        // This is used to Save State
        s3_layer_id: layer.id,
        s3_layer_type: 'wfs',
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
        'featureunselected': onFeatureUnselect,
        'loadstart': showThrobber,
        'loadend': hideThrobber,
        'loadcancel': hideThrobber
    });
    map.addLayer(wfsLayer);
    // Ensure Highlight & Popup Controls act on this layer
    S3.gis.layers_all.push(wfsLayer);
}

// WMS
function addWMSLayer(layer) {
    var name = layer.name;
    var url = layer.url;
    if ((undefined != layer.username) && (undefined != layer.password)) {
        var username = layer.username;
        var password = layer.password;
        url = url.replace('://', '://' + username + ':' + password + '@');
    }
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
    if (undefined != layer.legendURL) {
        var legendURL = layer.legendURL;
    } else {
        var legendURL;
    }

    var wmsLayer = new OpenLayers.Layer.WMS(
        name, url, {
            layers: layers
        },
        {
            dir: dir,
            wrapDateLine: true,
            isBaseLayer: isBaseLayer,
            transparent: transparent,
            // This is used to Save State
            s3_layer_id: layer.id,
            s3_layer_type: 'wms',
            // This gets picked up after mapPanel instantiates & copied to it's layerRecords
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
    if (legendURL) {
        // This gets picked up after mapPanel instantiates & copied to it's layerRecords
        wmsLayer.legendURL = legendURL;
    }
    map.addLayer(wmsLayer);
    if (layer._base) {
        map.setBaseLayer(wmsLayer);
    }
}

// XYZ
function addXYZLayer(layer) {
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
        var numZoomLevels = 19;
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

    var xyzLayer = new OpenLayers.Layer.XYZ(
        name, url, {
            dir: dir,
            // This is used to Save State
            s3_layer_id: layer.id,
            s3_layer_type: 'xyz',
            layername: layername,
            type: format,
            numZoomLevels: numZoomLevels
        }
    );

    if (undefined != layer.attribution) {
        xyzLayer.attribution = layer.attribution;
    }
    map.addLayer(xyzLayer);
    if (layer._base) {
        map.setBaseLayer(xyzLayer);
    }
}

// Support Vector Layers
function showThrobber() {
    $('#layer_throbber').show().removeClass('hide');
    S3.gis.layers_loading++;
}

function hideThrobber() {
    S3.gis.layers_loading--;
    if (S3.gis.layers_loading <= 0) {
        $('#layer_throbber').hide().addClass('hide');
    }
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
            // Resize when images are loaded
            //popup.registerImageListeners();
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
    if (feature.cluster) {
        // Cluster
        var name, uuid, url;
        var contents = S3.i18n.gis_cluster_multiple + ':<ul>';
        for (var i = 0; i < feature.cluster.length; i++) {
            name = feature.cluster[i].attributes.name;
            // @ToDo: Provide a way to load popups
            contents += '<li>' + name + '</li>';
        }
        contents += '</ul>';
        contents += "<div align='center'><a href='javascript:s3_gis_zoomToSelectedFeature(" + centerPoint.lon + "," + centerPoint.lat + ", 3)'>Zoom in</a></div>";
    } else {
        // Single Feature
        var attributes = feature.attributes;
        if (undefined != feature.style.balloonStyle) {
            // Use the provided BalloonStyle
            var balloonStyle = feature.style.balloonStyle;
            // "<strong>{name}</strong><br /><br />{description}"
            var contents = balloonStyle.replace(/{([^{}]*)}/g,
                function (a, b) {
                    var r = attributes[b];
                    return typeof r === 'string' || typeof r === 'number' ? r : a;
                }
            );
        } else {
            // Build the Popup contents manually
            var titleField = feature.layer.title;
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
                var row = '';
                if ('object' == type) {
                    // Geocommons style
                    var displayName = attributes[body[i]].displayName;
                    if (displayName == '') {
                        displayName = body[i];
                    }
                    var value = attributes[body[i]].value;
                    row = '<b>' + displayName + '</b>: ' + value + '<br />';
                } else if (undefined != attributes[body[i]]) {
                    row = attributes[body[i]] + '<br />';
                }
                content += row;
            }
            var contents = '<h3>' + title + '</h3>' + content;
        }
        // Protect the content against JavaScript attacks
        if (contents.search('<script') != -1) {
            contents = 'Content contained Javascript! Escaped content below.<br />' + contents.replace(/</g, '<');
        }
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
