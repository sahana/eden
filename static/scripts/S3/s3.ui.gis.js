/*
 * Map Widget
 */
(function(factory) {
    'use strict';
    // Use window. for Browser globals (not AMD or Node):
    factory(window.jQuery, window.ol);
})(function($, ol) {

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
            layers: {}          // Map Layers
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

            //this._serialize();
            //this._bindEvents();
        },

        /**
         * Add Layers to the Map
         */
        addLayers: function() {
            var configLayers = this.options.layers,
                layer,
                layers = [];

            // Base Layers
            // OpenStreetMap
            layer = new ol.layer.Tile({
                        source: new ol.source.OSM()
                    });
            layers.push(layer);

            // Overlays
            // Feature Layers
            var format,
                url,
                vectorLayers = configLayers.vector || [],
                vectorSource;

            for (var i=0; i < vectorLayers.length; i++) {

                layer = vectorLayers[i];

                if (undefined != layer.projection) {
                    format = new ol.format.GeoJSON({dataProjection: 'EPSG:' + layer.projection});
                } else {
                    // Feature Layers, GeoRSS & KML are always in 4326
                    format = new ol.format.GeoJSON({dataProjection: 'EPSG:4326'});
                }

                url = layer.url;
                if (!url.startsWith('http')) {
                    // Feature Layer read from this server
                    url = S3.Ap.concat(url);
                }

                vectorSource = new ol.source.Vector({
                    url: url,
                    format: format
                });

                layer = new ol.layer.Vector({
                    source: vectorSource//,
                    //style: styleFunction
                });
                layers.push(layer);
            }

            return layers;
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
         * (unused)
         *
         */
        _bindEvents: function() {

            //var self = this,
            //    ns = this.eventNamespace;

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
