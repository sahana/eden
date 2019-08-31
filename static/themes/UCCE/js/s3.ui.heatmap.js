/*
 * HeatMap Widget
 */
import { Map, View, getCenter, Feature, HeatmapLayer, ImageLayer, Point, Projection, Static, VectorSource } from './ol5.min.js';

(function(factory) {
    'use strict';
    // Use window. for Browser globals (not AMD or Node):
    factory(window.jQuery, Map, View, getCenter, Feature, HeatmapLayer, ImageLayer, Point, Projection, Static, VectorSource);
})(function($, Map, View, getCenter, Feature, HeatmapLayer, ImageLayer, Point, Projection, Static, VectorSource) {
    'use strict';
    var heatmapID = 0;

    $.widget('s3.heatMap', {

        /**
         * Options
         */
        options: {
        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = heatmapID;
            heatmapID += 1;
            this.eventNamespace = '.heatMap';

        },

        /**
         * Initialize the widget
         */
        _init: function(options) {

            /*
            var el = $(this.element),
                fieldname = el.attr('id');
            */

            this.heatMap();

            //this.refresh();

        },

        /**
          * Turn an Image into a (Heat)Map
          */
        heatMap: function() {

            var $this = $(this.element),
                $parent = $this.parent(),
                data = JSON.parse($this.val()),
                points = data.p,
                url = S3.Ap.concat('/default/download/' + data.i);

            // Add image to DOM to get the height/width
            $('<img>').attr('src', url).load(function() {
                var width = this.width,
                    height = this.height;

                // Map views always need a projection.  Here we just want to map image
                // coordinates directly to map coordinates, so we create a projection that uses
                // the image extent in pixels.
                var extent = [0, 0, width, height];
                var projection = new Projection({
                    code: 'base-image',
                    units: 'pixels',
                    extent: extent
                });

                var raster = new ImageLayer({
                    source: new Static({
                        url: url,
                        projection: projection,
                        imageExtent: extent
                    })
                });

                var source = new VectorSource({wrapX: false});

                var vector = new HeatmapLayer({
                    source: source,
                    gradient: ['#00AAA0', '#f00'], // $persian-green to red
                    blur: 7,   // default: 8 pixels
                    radius: 8  // default: 15 pixels
                });

                var map = new Map({
                    controls: [],
                    interactions: [],
                    layers: [
                      raster,
                      vector
                    ],
                    target: $parent.attr('id'),
                    view: new View({
                        projection: projection,
                        center: getCenter(extent),
                        zoom: 0,
                        maxZoom: 0
                    })
                });

                // We use simple coordinate pairs, not GeoJSON
                //const format = new GeoJSON({featureProjection: projection});

                // Add features
                var feature,
                    point;
                for (var i=0, len=points.length; i < len; i++) {
                    //geojson = JSON.parse(point);
                    //feature = format.readFeatureFromObject(geojson);
                    point = new Point(points[i]);
                    feature = new Feature(point);
                    feature.set('weight', 0.9); // This is about about Opacity...not how far along the gradient to colour
                    source.addFeature(feature);
                }

            });
        },

        /**
         * Unbind events (before refresh)
         *
        _unbindEvents: function() {

            var ns = this.eventNamespace;

            return true;
        }*/

    });
});
