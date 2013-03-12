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
    } catch(err) {}
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
    } catch(err) {}

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
        });
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
            var feature = S3.gis.format_geojson.parseFeature(S3.gis.features[i]);
            feature.geometry.transform(S3.gis.proj4326,
                                       S3.gis.projection_current);
            S3.gis.draftLayer.addFeatures([feature]);
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
    var layers;
    if (undefined != layer.layers) {
        layers = layer.layers;
    } else {
        // Default layer
        layers = 0;
    }
    var dir;
    if (undefined != layer.dir) {
        dir = layer.dir;
        if ( $.inArray(dir, S3.gis.dirs) == -1 ) {
            // Add this folder to the list of folders
            S3.gis.dirs.push(dir);
        }
    } else {
        // Default folder
        dir = '';
    }
    var isBaseLayer;
    if (undefined != layer.base) {
        isBaseLayer = layer.base;
    } else {
        isBaseLayer = false;
    }
    var transparent;
    if (undefined != layer.transparent) {
        transparent = layer.transparent;
    } else {
        transparent = true;
    }
    var visibility;
    if (undefined != layer.visibility) {
        visibility = layer.visibility;
    } else {
        // Default to visible
        visibility = true;
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
        i18n.gis_draft_layer, {
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
    var marker_url;
    if (undefined != layer.marker_image) {
        // per-Layer Marker
        marker_url = S3.gis.marker_url + layer.marker_image;
        var marker_height = layer.marker_height;
        var marker_width = layer.marker_width;
    } else {
        // per-Feature Marker or Shape
        marker_url = '';
    }
    var refresh;
    if (undefined != layer.refresh) {
        refresh = layer.refresh;
    } else {
        refresh = 900; // seconds (so 15 mins)
    }
    var dir;
    if (undefined != layer.dir) {
        dir = layer.dir;
        if ( $.inArray(dir, S3.gis.dirs) == -1 ) {
            // Add this folder to the list of folders
            S3.gis.dirs.push(dir);
        }
    } else {
        // Default folder
        dir = '';
    }
    var visibility;
    if (undefined != layer.visibility) {
        visibility = layer.visibility;
    } else {
        // Default to visible
        visibility = true;
    }
    var opacity;
    if (undefined != layer.opacity) {
        opacity = layer.opacity;
    } else {
        // Default to opaque
        opacity = 1;
    }
    var cluster_distance;
    if (undefined != layer.cluster_distance) {
        cluster_distance = layer.cluster_distance;
    } else {
        // Default to global settings
        cluster_distance = S3.gis.cluster_distance;
    }
    var cluster_threshold;
    if (undefined != layer.cluster_threshold) {
        cluster_threshold = layer.cluster_threshold;
    } else {
        // Default to global settings
        cluster_threshold = S3.gis.cluster_threshold;
    }
    var projection;
    if (undefined != layer.projection) {
        projection = layer.projection;
    } else {
        // Feature Layers, GeoRSS & KML are always in 4326
        projection = 4326;
    }
    if (4326 == projection) {
        projection = S3.gis.proj4326;
    } else {
        projection = new OpenLayers.Projection('EPSG:' + projection);
    }
    var layer_type;
    if (undefined != layer.type) {
        layer_type = layer.type;
    } else {
        // Feature Layers
        layer_type = 'feature';
    }
    var style;
    if (undefined != layer.style) {
        style = layer.style;
    } else {
        style = [];
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
            	var pix;
                if (feature.cluster) {
                    // Clustered Point
                    pix = '';
                } else if (feature.attributes.marker_width) {
                    // Use marker_width from feature
                    pix = feature.attributes.marker_width;
                } else {
                    // per-Layer Marker for Unclustered Point
                    pix = marker_width;
                }
                return pix;
            },
            graphicHeight: function(feature) {
            	var pix;
                if (feature.cluster) {
                    // Clustered Point
                    pix = '';
                } else if (feature.attributes.marker_height) {
                    // Use marker_height from feature
                    pix = feature.attributes.marker_height;
                } else {
                    // per-Layer Marker for Unclustered Point
                    pix = marker_height;
                }
                return pix;
            },
            graphicXOffset: function(feature) {
            	var pix;
                if (feature.cluster) {
                    // Clustered Point
                    pix = '';
                } else if (feature.attributes.marker_width) {
                    // Use marker_width from feature
                    pix = -(feature.attributes.marker_width / 2);
                } else {
                    // per-Layer Marker for Unclustered Point
                    pix = -(marker_width / 2);
                }
                return pix;
            },
            graphicYOffset: function(feature) {
            	var pix;
                if (feature.cluster) {
                    // Clustered Point
                    pix = '';
                } else if (feature.attributes.marker_height) {
                    // Use marker_height from feature
                    pix = -feature.attributes.marker_height;
                } else {
                    // per-Layer Marker for Unclustered Point
                    pix = -marker_height;
                }
                return pix;
            },
            graphicName: function(feature) {
            	var shape;
                if (feature.cluster) {
                    // Clustered Point
                    shape = 'circle';
                } else if (feature.attributes.shape) {
                    // Use shape from feature
                    shape = feature.attributes.shape;
                } else {
                    // default to a Circle
                    shape = 'circle';
                }
                return shape;
            },
            externalGraphic: function(feature) {
            	var url;
                if (feature.cluster) {
                    // Clustered Point
                    url = '';
                } else if (feature.attributes.marker_url) {
                    // Use marker from feature
                    url = feature.attributes.marker_url;
                } else {
                    // per-Layer Marker for Unclustered Point
                    url = marker_url;
                }
                return url;
            },
            radius: function(feature) {
            	var pix;
                if (feature.cluster) {
                    // Size for Clustered Point
                    pix = Math.min(feature.attributes.count/2, 8) + 10;
                } else if (feature.attributes.size) {
                    // Use size from feature
                    pix = feature.attributes.size;
                } else {
                    // default Size for Unclustered Point
                    pix = 10;
                }
                return pix;
            },
            fill: function(feature) {
            	var color;
                if (feature.cluster) {
                    if (feature.cluster[0].attributes.colour) {
                        // Use colour from features
                        color = feature.cluster[0].attributes.colour;
                    } else {
                        // default fillColor for Clustered Point
                        color = '#8087ff';
                    }
                } else if (feature.attributes.colour) {
                    // Feature Query: Use colour from feature
                    color = feature.attributes.colour;
                } else if (style.length) {
                    // Theme Layer: Lookup colour from style rule
                    var value = feature.attributes.value;
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
                    color = '#f5902e';
                }
                return color;
            },
            fillOpacity: function(feature) {
            	var fill_opacity;
                if (feature.cluster) {
                    if (feature.cluster[0].attributes.opacity) {
                        // Use opacity from features
                        fill_opacity = feature.cluster[0].attributes.opacity;
                    } else {
                        // default fillOpacity for Clustered Point
                        fill_opacity = opacity;
                    }
                } else if (feature.attributes.opacity) {
                    // Use opacity from feature
                    fill_opacity = feature.attributes.opacity;
                } else {
                    // default fillOpacity for Unclustered Point
                    fill_opacity = opacity;
                }
                return fill_opacity;
            },
            stroke: function(feature) {
            	var color;
                if (feature.cluster) {
                    if (feature.cluster[0].attributes.colour) {
                        // Use colour from features
                        color = feature.cluster[0].attributes.colour;
                    } else {
                        // default strokeColor for Clustered Point
                        color = '#2b2f76';
                    }
                } else if (feature.attributes.colour) {
                    // Feature Query: Use colour from feature
                    color = feature.attributes.colour;
                } else if (style.length) {
                    // Theme Layer: Lookup colour from style rule
                    var value = feature.attributes.value;
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
                    color = '#f5902e';
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
        'loadstart': function(event) {
            showThrobber(event.object.s3_layer_id);
        },
        'loadend': function(event) {
            hideThrobber(event.object.s3_layer_id);
        }
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
    var waypoints;
    if (undefined != layer.waypoints) {
        waypoints = layer.waypoints;
    } else {
        waypoints = true;
    }
    var tracks;
    if (undefined != layer.tracks) {
        tracks = layer.tracks;
    } else {
        tracks = true;
    }
    var routes;
    if (undefined != layer.routes) {
        routes = layer.routes;
    } else {
        routes = true;
    }
    var visibility;
    if (undefined != layer.visibility) {
        visibility = layer.visibility;
    } else {
        visibility = true;
    }
    var dir;
    if (undefined != layer.dir) {
        dir = layer.dir;
        if ( $.inArray(dir, S3.gis.dirs) == -1 ) {
            // Add this folder to the list of folders
            S3.gis.dirs.push(dir);
        }
    } else {
        // Default folder
        dir = '';
    }
    var opacity;
    if (undefined != layer.opacity) {
        opacity = layer.opacity;
    } else {
        opacity = 1;
    }
    var cluster_distance;
    if (undefined != layer.cluster_distance) {
        cluster_distance = layer.cluster_distance;
    } else {
        cluster_distance = S3.gis.cluster_distance;
    }
    var cluster_threshold;
    if (undefined != layer.cluster_threshold) {
        cluster_threshold = layer.cluster_threshold;
    } else {
        cluster_threshold = S3.gis.cluster_threshold;
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
        'loadstart': function(event) {
            showThrobber(event.object.s3_layer_id);
        },
        'loadend': function(event) {
            hideThrobber(event.object.s3_layer_id);
        }
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
    var title;
    if (undefined != layer.title) {
        title = layer.title;
    } else {
        title = 'name';
    }
    var body;
    if (undefined != layer.body) {
        body = layer.body;
    } else {
        body = 'description';
    }
    var refresh;
    if (undefined != layer.refresh) {
        refresh = layer.refresh;
    } else {
        refresh = 900; // seconds (so 15 mins)
    }
    var visibility;
    if (undefined != layer.visibility) {
        visibility = layer.visibility;
    } else {
        // Default to visible
        visibility = true;
    }
    var dir;
    if (undefined != layer.dir) {
        dir = layer.dir;
        if ( $.inArray(dir, S3.gis.dirs) == -1 ) {
            // Add this folder to the list of folders
            S3.gis.dirs.push(dir);
        }
    } else {
        // Default folder
        dir = '';
    }
    var opacity;
    if (undefined != layer.opacity) {
        opacity = layer.opacity;
    } else {
        opacity = 1;
    }
    var cluster_distance;
    if (undefined != layer.cluster_distance) {
        cluster_distance = layer.cluster_distance;
    } else {
        cluster_distance = S3.gis.cluster_distance;
    }
    var cluster_threshold;
    if (undefined != layer.cluster_threshold) {
        cluster_threshold = layer.cluster_threshold;
    } else {
        cluster_threshold = S3.gis.cluster_threshold;
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
            	var pix;
                if (feature.cluster) {
                    // Clustered Point
                    pix = '';
                } else {
                    pix = S3.gis.image.width;
                }
                return pix;
            },
            graphicHeight: function(feature) {
            	var pix;
                if (feature.cluster) {
                    // Clustered Point
                    pix = '';
                } else {
                    pix = S3.gis.image.height;
                }
                return pix;
            },
            graphicXOffset: function(feature) {
            	var pix;
                if (feature.cluster) {
                    // Clustered Point
                    pix = '';
                } else {
                    pix = -(S3.gis.image.width / 2);
                }
                return pix;
            },
            graphicYOffset: function(feature) {
            	var pix;
                if (feature.cluster) {
                    // Clustered Point
                    pix = '';
                } else {
                    pix = -S3.gis.image.height;
                }
                return pix;
            },
            externalGraphic: function(feature) {
            	var url;
                if (feature.cluster) {
                    // Clustered Point
                    url = '';
                } else {
                    url = marker_url;
                }
                return url;
            },
            radius: function(feature) {
            	var pix;
                if (feature.cluster) {
                    // Size for Clustered Point
                    pix = Math.min(feature.attributes.count/2, 8) + 10;
                } else {
                    // default Size for Unclustered Point
                    pix = 10;
                }
                return pix;
            },
            fill: function(feature) {
            	var color;
                if (feature.cluster) {
                    // default fillColor for Clustered Point
                    color = '#8087ff';
                } else {
                    // default fillColor for Unclustered Point
                    color = '#f5902e';
                }
                return color;
            },
            stroke: function(feature) {
            	var color;
                if (feature.cluster) {
                    // default strokeColor for Clustered Point
                    color = '#2b2f76';
                } else {
                    // default strokeColor for Unclustered Point
                    color = '#f5902e';
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
        'loadstart': function(event) {
            showThrobber(event.object.s3_layer_id);
        },
        'loadend': function(event) {
            hideThrobber(event.object.s3_layer_id);
        }
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
};

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
    var visibility;
    if (undefined != layer.visibility) {
        visibility = layer.visibility;
    } else {
        // Default to visible
        visibility = true;
    }
    var dir;
    if (undefined != layer.dir) {
        dir = layer.dir;
        if ( $.inArray(dir, S3.gis.dirs) == -1 ) {
            // Add this folder to the list of folders
            S3.gis.dirs.push(dir);
        }
    } else {
        // Default folder
        dir = '';
    }
    var isBaseLayer;
    if (undefined != layer.base) {
        isBaseLayer = layer.base;
    } else {
        isBaseLayer = true;
    }
    var numZoomLevels;
    if (undefined != layer.zoomLevels) {
        numZoomLevels = layer.zoomLevels;
    } else {
        numZoomLevels = 19;
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
        layer.setVisibility(owm.station.visibility);
        layer.events.on({
            'featureselected': layer.onSelect,
            'featureunselected': layer.onUnselect,
            'loadstart': function(event) {
                showThrobber(event.object.s3_layer_id);
            },
            'loadend': function(event) {
                hideThrobber(event.object.s3_layer_id);
            }
        });
        map.addLayer(layer);
        // Ensure Highlight & Popup Controls act on this layer
        S3.gis.layers_all.push(layer);
    }
    if (owm.city) {
        layer = new OpenLayers.Layer.Vector.OWMWeather(
            owm.city.name,
            {dir: owm.city.dir,
             // This is used to Save State
             s3_layer_id: owm.city.id,
             s3_layer_type: 'openweathermap'
            }
        );
        layer.setVisibility(owm.city.visibility);
        layer.events.on({
            'featureselected': layer.onSelect,
            'featureunselected': layer.onUnselect,
            'loadstart': function(event) {
                showThrobber(event.object.s3_layer_id);
            },
            'loadend': function(event) {
                hideThrobber(event.object.s3_layer_id);
            }
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
    var numZoomLevels;
    if (undefined != layer.zoomLevels) {
        numZoomLevels = layer.zoomLevels;
    } else {
        numZoomLevels = 19;
    }
    var dir;
    if (undefined != layer.dir) {
        dir = layer.dir;
        if ( $.inArray(dir, S3.gis.dirs) == -1 ) {
            // Add this folder to the list of folders
            S3.gis.dirs.push(dir);
        }
    } else {
        // Default folder
        dir = '';
    }
    var format;
    if (undefined != layer.format) {
        format = layer.format;
    } else {
        format = 'png';
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
    var version;
    if (undefined != layer.version) {
    	version = layer.version;
    } else {
        version = '1.1.0';
    }
    var geometryName;
    if (undefined != layer.geometryName) {
        geometryName = layer.geometryName;
    } else {
        geometryName = 'the_geom';
    }
    var styleField;
    if (undefined != layer.styleField) {
        styleField = layer.styleField;
    } else {
        styleField = '';
    }
    var styleValues;
    if (undefined != layer.styleValues) {
        styleValues = layer.styleValues;
    } else {
        styleValues = {};
    }
    var visibility;
    if (undefined != layer.visibility) {
        visibility = layer.visibility;
    } else {
        // Default to visible
        visibility = true;
    }
    var dir;
    if (undefined != layer.dir) {
        dir = layer.dir;
        if ( $.inArray(dir, S3.gis.dirs) == -1 ) {
            // Add this folder to the list of folders
            S3.gis.dirs.push(dir);
        }
    } else {
        // Default folder
        dir = '';
    }
    var opacity;
    if (undefined != layer.opacity) {
        opacity = layer.opacity;
    } else {
        opacity = 1;
    }
    var cluster_distance;
    if (undefined != layer.cluster_distance) {
        cluster_distance = layer.cluster_distance;
    } else {
        cluster_distance = S3.gis.cluster_distance;
    }
    var cluster_threshold;
    if (undefined != layer.cluster_threshold) {
        cluster_threshold = layer.cluster_threshold;
    } else {
        cluster_threshold = S3.gis.cluster_threshold;
    }
    var projection;
    var srsName;
    if (undefined != layer.projection) {
        projection = layer.projection;
        srsName = 'EPSG:' + projection;
    } else {
        projection = '4326';
        srsName = 'EPSG:4326';
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
    });

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
    };

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

    if ('4326' == projection) {
        projection = S3.gis.proj4326;
    } else {
        projection = new OpenLayers.Projection('EPSG:' + projection);
    }

    // Put these in Global Scope & i18n the messages
    //function showSuccessMsg(){
    //    showMsg("Transaction successfully completed");
    //}
    //function showFailureMsg(){
    //    showMsg("An error occured while operating the transaction");
    //}
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
        'loadstart': function(event) {
            showThrobber(event.object.s3_layer_id);
        },
        'loadend': function(event) {
            hideThrobber(event.object.s3_layer_id);
        }
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
    var visibility;
    if (undefined != layer.visibility) {
        visibility = layer.visibility;
    } else {
        visibility = true;
    }
    var dir;
    if (undefined != layer.dir) {
        dir = layer.dir;
        if ( $.inArray(dir, S3.gis.dirs) == -1 ) {
            // Add this folder to the list of folders
            S3.gis.dirs.push(dir);
        }
    } else {
        // Default folder
        dir = '';
    }
    var isBaseLayer;
    if (undefined != layer.base) {
        isBaseLayer = layer.base;
    } else {
        isBaseLayer = false;
    }
    var transparent;
    if (undefined != layer.transparent) {
        transparent = layer.transparent;
    } else {
        transparent = true;
    }
    var format;
    if (undefined != layer.format) {
        format = layer.format;
    } else {
        format = 'image/png';
    }
    var version;
    if (undefined != layer.version) {
        version = layer.version;
    } else {
        version = '1.1.1';
    }
    var wms_map;
    if (undefined != layer.map) {
        wms_map = layer.map;
    } else {
        wms_map = '';
    }
    var style;
    if (undefined != layer.style) {
        style = layer.style;
    } else {
        style = '';
    }
    var bgcolor;
    if (undefined != layer.bgcolor) {
        bgcolor = '0x' + layer.bgcolor;
    } else {
        bgcolor = '';
    }
    var buffer;
    if (undefined != layer.buffer) {
        buffer = layer.buffer;
    } else {
        buffer = 0;
    }
    var tiled;
    if (undefined != layer.tiled) {
        tiled = layer.tiled;
    } else {
        tiled = false;
    }
    var opacity;
    if (undefined != layer.opacity) {
        opacity = layer.opacity;
    } else {
        opacity = 1;
    }
    var queryable;
    if (undefined != layer.queryable) {
        queryable = layer.queryable;
    } else {
        queryable = 1;
    }
    var legendURL;
    if (undefined != layer.legendURL) {
        legendURL = layer.legendURL;
    }

    var wmsLayer = new OpenLayers.Layer.WMS(
        name, url, {
            layers: layers,
            transparent: transparent
        },
        {
            dir: dir,
            wrapDateLine: true,
            isBaseLayer: isBaseLayer,
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
    var numZoomLevels;
    if (undefined != layer.zoomLevels) {
        numZoomLevels = layer.zoomLevels;
    } else {
        numZoomLevels = 19;
    }
    var dir;
    if (undefined != layer.dir) {
        dir = layer.dir;
        if ( $.inArray(dir, S3.gis.dirs) == -1 ) {
            // Add this folder to the list of folders
            S3.gis.dirs.push(dir);
        }
    } else {
        // Default folder
        dir = '';
    }
    var format;
    if (undefined != layer.format) {
        format = layer.format;
    } else {
        format = 'png';
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
function showThrobber(id) {
    $('#layer_throbber').show().removeClass('hide');
    S3.gis.layers_loading.pop(id); // we never want 2 pushed
    S3.gis.layers_loading.push(id);
}

function hideThrobber(id) {
    S3.gis.layers_loading.pop(id);
    if (S3.gis.layers_loading.length === 0) {
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
                msg = i18n.gis_requires_login;
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
    var contents;
    var name;
    if (feature.cluster) {
        // Cluster
        var uuid, url;
        contents = i18n.gis_cluster_multiple + ':<ul>';
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
            contents = i18n.gis_loading + "...<img src='" + S3.gis.ajax_loader + "' border=0 />";
        } else {
            // Popup contents are built from the attributes
            if (undefined == feature.attributes.name) {
                name = '';
            } else {
                name = '<h3>' + feature.attributes.name + '</h3>';
            }
            var description;
            if (undefined == feature.attributes.description) {
                description = '';
            } else {
                description = '<p>' + feature.attributes.description + '</p>';
            }
            var link;
            if (undefined == feature.attributes.link) {
                link = '';
            } else {
                link = '<a href="' + feature.attributes.link + '" target="_blank">' + feature.attributes.link + '</a>';
            }
            var data;
            if (undefined == feature.attributes.data) {
                data = '';
            } else if (feature.attributes.data.indexOf('http://') === 0) {
                data_link = true;
                var data_id = S3.uid();
                data = '<div id="' + data_id + '">' + i18n.gis_loading + "...<img src='" + S3.gis.ajax_loader + "' border=0 />" + '</div>';
            } else {
                data = '<p>' + feature.attributes.data + '</p>';
            }
            var image;
            if (undefined == feature.attributes.image) {
                image = '';
            } else if (feature.attributes.image.indexOf('http://') === 0) {
                image = '<img src="' + feature.attributes.image + '" height=300 width=300>';
            } else {
                image = '';
            }
            contents = name + description + link + data + image;
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
    var contents;
    if (feature.cluster) {
        // Cluster
        var name, uuid, url;
        contents = i18n.gis_cluster_multiple + ':<ul>';
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
            contents = balloonStyle.replace(/{([^{}]*)}/g,
                function (a, b) {
                    var r = attributes[b];
                    return typeof r === 'string' || typeof r === 'number' ? r : a;
                }
            );
        } else {
            // Build the Popup contents manually
            var titleField = feature.layer.title;
            var type = typeof attributes[titleField];
            var title;
            if ('object' == type) {
                title = attributes[titleField].value;
            } else {
                title = attributes[titleField];
            }
            var body = feature.layer.body.split(' ');
            content = '';
            for (var j = 0; j < body.length; j++) {
                type = typeof attributes[body[j]];
                var row = '';
                if ('object' == type) {
                    // Geocommons style
                    var displayName = attributes[body[j]].displayName;
                    if (displayName === '') {
                        displayName = body[j];
                    }
                    var value = attributes[body[j]].value;
                    row = '<b>' + displayName + '</b>: ' + value + '<br />';
                } else if (undefined != attributes[body[j]]) {
                    row = attributes[body[j]] + '<br />';
                }
                content += row;
            }
            contents = '<h3>' + title + '</h3>' + content;
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
    var contents;
    if (feature.cluster) {
        // Cluster
        var name;
        contents = i18n.gis_cluster_multiple + ':<ul>';
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
        contents = '<h3>' + title + '</h3>' + content;
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
