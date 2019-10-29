/*
 * Map Widget
 */
import {Map,
        View,
        Draw,
        Fill,
        GeoJSON,
        getCenter,
        //HeatMapLayer,
        //ImageLayer,
        OSM,
        Projection,
        //Static,
        Stroke,
        Style,
        TileLayer,
        VectorLayer,
        VectorSource
        } from '../gis/ol6.min.js';

(function(factory) {
    'use strict';
    // Use window. for Browser globals (not AMD or Node):
    factory(window.jQuery,
            //window.loadImage,
            Map,
            View,
            Draw,
            Fill,
            GeoJSON,
            getCenter,
            //HeatMapLayer,
            //ImageLayer,
            OSM,
            Projection,
            //Static,
            Stroke,
            Style,
            TileLayer,
            VectorLayer,
            VectorSource
            );
})(function($,
            //loadImage,
            Map,
            View,
            Draw,
            Fill,
            GeoJSON,
            getCenter,
            //HeatMapLayer,
            //ImageLayer,
            OSM,
            Projection,
            //Static,
            Stroke,
            Style,
            TileLayer,
            VectorLayer,
            VectorSource
            ) {

    'use strict';
    var mapID = 0;

    $.widget('s3.showMap', {

        /**
         * Options
         */
        options: {
            id: 'default_map',  // Map ID (Div)
            height: 400,        // Map Height (pixels)
            width: 400,         // Map Width (pixels)
            lat: 0,             // Center Lat
            lon: 0,             // Center Lon
            projection: 900913, // EPSG:900913 = Spherical Mercator
            zoom: 0             // Map Zoom
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
            this._unbindEvents();
            this._deserialize();

            var options = this.options;

            // Map views always need a projection
            /*
            var extent = [0, 0, width, height];
            var projection = new Projection({
                extent: extent
            });*/

            var map = new Map({
                layers: [
                    new TileLayer({
                        source: new OSM()
                    })
                ],
                target: options.id,
                view: new View({
                    center: [options.lat,
                             options.lon
                             ],
                    zoom: options.zoom
                })
            });

            //this._serialize();
            this._bindEvents();
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
        _bindEvents: function() {

            var self = this,
                ns = this.eventNamespace;

        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var ns = this.eventNamespace;

            return true;
        }

    });
});
