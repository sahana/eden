/* Copyright (c) 2014 by Sahana Software Foundation.
 * Published under the MIT license.
 * See LICENSE in the Sahana Eden distribution or repository for the
 * full text of the license. */

/**
 * @requires OpenLayers/Strategy/BBOX.js
 */

/**
 * Class: OpenLayers.Strategy.ZoomBBOX
 * A strategy that reads new features when the viewport invalidates
 *     some bounds (BBOX) and also re-requests features for different
 *     zoom levels.
 *
 * Inherits from:
 *  - <OpenLayers.Strategy.BBOX>
 */
OpenLayers.Strategy.ZoomBBOX = OpenLayers.Class(OpenLayers.Strategy.BBOX, {
    
    /**
     * Property: zoom
     * {Integer} Last zoom
     */
    zoom: null,

    /**
     * Property: center
     * {Integer} Last center
     */
    center: null,

    /**
     * Property: level
     * {String} Last level; detect level changes
     */
    level: null,

    /**
     * Property: levels
     * {Array} Default Mapping of Zoom levels to Location Hierarchy levels
     *
     * @ToDo: This needs to vary by center point as different countries vary a lot here
     *        - have a default lookup list and then allow specification of Polygons (e.g. BBOXes) for exception cases
     */
    levels: {0: 0,
             1: 0,
             2: 0,
             3: 0,
             4: 1,
             5: 1,
             6: 1,
             7: 2,
             8: 2,
             9: 3,
             10: 3,
             11: 3,
             12: 3,
             13: 4,
             14: 4,
             15: 5,
             16: 5,
             // @ToDo: Individual Features (Clustered if-necessary)
             17: 5,
             18: 5
             },

    /**
     * Property: exceptions
     * {Array} Exception Mappings of Zoom levels to Location Hierarchy levels
     * - provides OpenLayers.Geometry areas which have a different set of mappings
     *
     */
    exceptions: {},

    /**
     * Method: getLevel
     *
     * Parameters:
     * center - {OpenLayers.LonLat}
     * zoom - {Integer}
     *
     * Returns:
     * {<OpenLayers.Protocol.Response>} The protocol response object
     *      returned by the layer protocol.
     */
    getLevel: function(center, zoom) {
        // @ToDo: If we have feastures then vary the zoom, based on their size
        // (i.e. Do this introspectively not by pre-planned exceptions)
        //var features = this.layer.features;
        //for
        //var size = feature.geometry.getBounds().getSize()
        //if (feature.geometry.intersects(geom))
        var level = 'L' + this.levels[zoom];
        return level;
    },
 
    /**
     * Method: update
     * Callback function called on "moveend" or "refresh" layer events.
     *
     * Parameters:
     * options - {Object} Optional object whose properties will determine
     *     the behaviour of this Strategy
     *
     * Valid options include:
     * force - {Boolean} if true, new data must be unconditionally read.
     * noAbort - {Boolean} if true, do not abort previous requests.
     */
    update: function(options) {
        var layer = this.layer;
        var old_level = this.getLevel(this.center, this.zoom);
        var center = layer.map.getCenter();
        var zoom = layer.map.getZoom();
        var new_level = this.getLevel(center, zoom);
        this.level = new_level;
        this.center = center;
        this.zoom = zoom;
        var mapBounds = this.getMapBounds();
        if (mapBounds !== null && ((options && options.force) ||
            (layer.visibility && layer.calculateInRange() && this.invalidBounds(mapBounds)) ||
            new_level != old_level)) {
            this.calculateBounds(mapBounds);
            this.resolution = layer.map.getResolution();
            this.triggerRead(options);
        }
    },

    /**
     * Method: triggerRead
     *
     * Parameters:
     * options - {Object} Additional options for the protocol's read method 
     *     (optional)
     *
     * Returns:
     * {<OpenLayers.Protocol.Response>} The protocol response object
     *      returned by the layer protocol.
     */
    triggerRead: function(options) {
        var layer = this.layer;
        var response = this.response;
        if (response && !(options && options.noAbort === true)) {
            layer.protocol.abort(response);
            layer.events.triggerEvent('loadend');
        }
        var evt = {filter: this.createFilter()};
        layer.events.triggerEvent('loadstart', evt);
        response = layer.protocol.read(
            OpenLayers.Util.applyDefaults({
                filter: evt.filter,
                callback: this.merge,
                params: {level: this.level},
                scope: this
        }, options));
    },
 
    CLASS_NAME: "OpenLayers.Strategy.ZoomBBOX" 
});
