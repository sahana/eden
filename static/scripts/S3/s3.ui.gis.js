/*
 * Map Widget
 */
(function(factory) {
    'use strict';
    // Use window. for Browser globals (not AMD or Node):
    factory(window.jQuery, window._, window.ol);
})(function($, _, ol) {

    'use strict';
    var mapID = 0;

    $.widget('s3.showMap', {

        /**
         * Options
         */
        options: {
            id: 'default_map',  // Map ID (Div)
            //height: 400,        // Map Height (pixels)
            //width: 400,         // Map Width (pixels)
            lat: 0,             // Center Lat
            lon: 0,             // Center Lon
            //projection: 3857,  // EPSG:3857 = Spherical Mercator
            zoom: 0,            // Map Zoom
            layers_osm: []      // OpenStreetMap Layers
        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = mapID;
            mapID += 1;
            this.eventNamespace = '.s3Map';

        },

        /**
         * Initialize the widget
         */
        _init: function(options) {

            //var el = $(this.element);

            // Flag for whether a tooltip is showing
            //self.tooltip = false;

            this.refresh();

        },

        /**
          * Remove generated elements & reset other changes
          */
        _destroy: function() {
            $.Widget.prototype.destroy.call(this);
        },

        /**
         * Redraw widget contents
         */
        refresh: function() {
            //this._unbindEvents();
            //this._deserialize();

            var options = this.options;

            // Map views always need a projection
            /*
            var extent = [0, 0, width, height]; // for ImageMap
            var projection = new ol.proj.Projection({
                extent: extent
            });*/

            var layers = this.addLayers();

            var map = new ol.Map({
                layers: layers,
                target: options.id,
                view: new ol.View({
                    center: ol.proj.fromLonLat([options.lon, options.lat]),
                    zoom: options.zoom
                })
            });

            // Tooltip
            var tooltip = $('#' + this.options.id + ' .s3-gis-tooltip');
            this.tooltip = tooltip;

            var tooltip_ol = new ol.Overlay({
                element: tooltip[0],
                positioning: 'bottom-center',
                stopEvent: false,
                offset: [0, -50]
            });
            map.addOverlay(tooltip_ol);
            this.tooltip_ol = tooltip_ol;

            //this._serialize();
            this._bindEvents(map);
        },

        /**
         * Add Layers to the Map
         */
        addLayers: function() {
            var layers = [];

            // OpenStreetMap
            this.addLayersOSM(layers);

            // GeoJSON Layers
            this.addLayersGeoJSON(layers);

            return layers;
        },

        /**
         * Add OSM Layers to the Map
         */
        addLayersOSM: function(layers) {
            var attributions,
                base,
                layer,
                layers_osm = this.options.layers_osm || [],
                maxZoom,
                opaque,
                options,
                url;

            for (var i=0; i < layers_osm.length; i++) {

                layer = layers_osm[i];

                if (undefined != layer.attribution) {
                    attributions = [layer.attribution];
                } else {
                    attributions = [ol.source.OSM.ATTRIBUTION];
                }

                if (undefined != layer.maxZoom) {
                    maxZoom = layer.maxZoom;
                } else {
                    maxZoom = 19;
                }

                if (undefined != layer.base) {
                    opaque = layer.base;
                } else {
                    opaque = true;
                }

                if (undefined != layer.url) {
                    url = layer.url;
                } else {
                    url = 'https://{a-c}.tile.openstreetmap.org/{z}/{x}/{y}.png';
                }

                options = {attributions: attributions,
                           maxZoom: maxZoom,
                           opaque: opaque,
                           url: url
                           }
                layers.push(new ol.layer.Tile({
                                source: new ol.source.OSM(options)
                            }));
            }
        },

        /**
         * Add GeoJSON Layers to the Map
         *
         * @ToDo: Combine these 7 layer types server-side to save a little bandwidth
         */
        addLayersGeoJSON: function(layers) {
            var options = this.options,
                feature_queries = options.feature_queries || [],
                feature_resources = options.feature_resources || [],
                format,
                layer,
                layerType,
                layers_feature = options.layers_feature || [],
                layers_geojson = options.layers_geojson || [],
                layers_georss = options.layers_georss || [],
                layers_shapefile = options.layers_shapefile || [],
                layers_theme = options.layers_theme || [],
                s3_popup_format,
                style,
                url,
                vectorLayer,
                vectorLayers = [],
                vectorSource;

            vectorLayers = feature_queries.concat(feature_resources)
                                          .concat(layers_feature)
                                          .concat(layers_geojson)
                                          .concat(layers_georss)
                                          .concat(layers_shapefile)
                                          .concat(layers_theme);

            for (var i=0; i < vectorLayers.length; i++) {

                layer = vectorLayers[i];

                if (undefined != layer.projection) {
                    format = new ol.format.GeoJSON({dataProjection: 'EPSG:' + layer.projection});
                } else {
                    // Feature Layers, GeoRSS & KML are always in 4326
                    format = new ol.format.GeoJSON({dataProjection: 'EPSG:4326'});
                }

                style = this.layerStyle(layer);

                url = layer.url;
                /* @ToDo: Optimise by not xferring appname
                if (!url.startsWith('http')) {
                    // Feature Layer read from this server
                    url = S3.Ap.concat(url);
                } */

                vectorSource = new ol.source.Vector({
                    url: url,
                    format: format
                });

                vectorLayer = new ol.layer.Vector({
                    source: vectorSource,
                    style: style
                });

                // Set the popup_format, even if empty
                // - leave if not set (e.g. Feature Queries)
                if (undefined != layer.popup_format) {
                    vectorLayer.s3_popup_format = layer.popup_format;
                }

                if (undefined != layer.type) {
                    layerType = layer.type;
                } else {
                    // Feature Layers
                    layerType = 'feature';
                }
                vectorLayer.s3_layer_type = layerType;

                layers.push(vectorLayer);
            }
        },

        /**
         * Style a Vector Layer
         */
        layerStyle: function(layer) {

            var style;

            if (undefined !== layer.marker) {
                // Style all features with layer.marker
                style = new ol.style.Style({
                    image: new ol.style.Icon({
                        // @ToDo: Allow external markers prefixed by http
                        // @ToDo: Optimise Marker for ol6 by not xferring the h/w
                        src: S3.Ap.concat('/static/img/markers/' + layer.marker.i)
                    })
                });
            } else if (undefined !== layer.marker) {
                // Style features using layer.style
                style = layer.style;
            } else {
                // Default Style
                var fill = new ol.style.Fill({
                    color: 'rgba(255,255,255,0.4)'
                });
                var stroke = new ol.style.Stroke({
                    color: '#3399CC',
                    width: 1.25
                });
                var image = new ol.style.Icon({
                    src: S3.Ap.concat('/static/img/markers/' + this.options.marker)
                })
                var styles = {
                    'Point': new ol.style.Style({
                        image: image
                    }),
                    'LineString': new ol.style.Style({
                        stroke: stroke
                    }),
                    'MultiLineString': new ol.style.Style({
                        stroke: stroke
                    }),
                    'MultiPoint': new ol.style.Style({
                        image: image
                    }),
                    'MultiPolygon': new ol.style.Style({
                        stroke: stroke,
                        fill: fill
                    }),
                    'Polygon': new ol.style.Style({
                        stroke: stroke,
                        fill: fill
                    }),
                    'GeometryCollection': new ol.style.Style({
                        stroke: stroke,
                        fill: fill,
                        image: image
                    }),
                    'Circle': new ol.style.Style({
                        stroke: stroke,
                        fill: fill
                    })
                };
                style = function(feature) {
                    return styles[feature.getGeometry().getType()];
                };
            }
            return style;

        },
        /**
         * Encode this.data as JSON and write into real input
         *
         * (unused)
         *
         * @returns {JSON} the JSON data
         *
        _serialize: function() {

            var json = JSON.stringify(this.data);
            $(this.element).val(json);
            return json;

        },*/

        /**
         * Parse the JSON from real input into this.data
         *
         * (unused)
         *
         * @returns {object} this.data
         */
        _deserialize: function() {

            //var value = $(this.element).val() || '{}';
            //this.data = JSON.parse(value);
            //return this.data;

        },

        /**
         * Bind event handlers (after refresh)
         *
         */
        _bindEvents: function(map) {

            var self = this,
                //ns = this.eventNamespace,
                attributes,
                content,
                coordinates,
                defaults,
                feature,
                key,
                keys,
                layer,
                popup_format,
                results,
                template;

            // Show Tooltip when hovering over marker
            map.on('pointermove', function(e) {
                if (e.dragging) {
                    self.tooltip.hide();
                    return;
                }
                results = map.forEachFeatureAtPixel(e.pixel, function(feature, layer) {
                    return {feature: feature,
                            layer: layer
                            };
                });
                if (results) {
                    feature = results.feature;
                    layer = results.layer;
                    coordinates = feature.getGeometry().getCoordinates();
                    self.tooltip_ol.setPosition(coordinates);

                    if (undefined != layer.s3_popup_format) {
                        // GeoJSON Feature Layers
                        _.templateSettings = {interpolate: /\{(.+?)\}/g};
                        popup_format = layer.s3_popup_format;
                        template = _.template(popup_format);
                        // Ensure we have all keys (we don't transmit empty attr)
                        attributes = {};//= feature.getProperties()
                        defaults = {};
                        keys = popup_format.split('{');
                        for (var i = 0; i < keys.length; i++) {
                            key = keys[i].split('}')[0];
                            attributes[key] = feature.get(key);
                            defaults[key] = '';
                        }
                        _.defaults(attributes, defaults);
                        content = template(attributes);
                    } else if (undefined != attributes.popup) {
                        // Feature Queries or Theme Layers
                        content = feature.get('popup');
                    } else if (undefined != feature.get('name')) {
                        // GeoJSON, GeoRSS or Legacy Features
                        content = feature.get('name');
                    } else if (undefined != layer.title) {
                        // KML or WFS
                        var a = feature.get(layer.title);
                        var type = typeof a;
                        if ('object' == type) {
                            content = a.value;
                        } else {
                            content = a;
                        }
                    }

                    self.tooltip.html(content).show();

                } else {
                    self.tooltip.hide();
                }
            });

            // Show Popup when clicking on a marker
            map.on('click', function(e) {
                results = map.forEachFeatureAtPixel(e.pixel, function(feature, layer) {
                    return {feature: feature,
                            layer: layer
                            };
                });
                if (results) {
                    // Close the tooltip
                    self.tooltip.hide();

                    feature = results.feature;
                    layer = results.layer;

                }
            });

        },

        /**
         * Unbind events (before refresh)
         *
         * (unused)
         */
        _unbindEvents: function() {

            //var ns = this.eventNamespace;

            return true;
        }

    });
});
