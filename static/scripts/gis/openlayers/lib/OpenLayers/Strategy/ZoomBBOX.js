/* Copyright (c) 2014 by Sahana Software Foundation.
 * Published under the MIT license.
 * See LICENSE in the Sahana Eden distribution or repository for the
 * full text of the license. */

/**
 * @requires OpenLayers/Strategy/BBOX.js
 * @requires OpenLayers/Filter/Spatial.js
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
     * {Integer} Last zoom; detect zoom changes
     */
    zoom: null,

    /**
     * Property: levels
     * {Array} Mapping of zoom levels to Location Hierarchy levels
     *
     * @ToDo: This needs to vary by BBOX as different countries vary a lot here
     */
    /*
    levels: {0-3: 0,
             4-6: 1,
             7-8: 2,
             9-12: 3,
             13-14: 4,
             15-16: 4,
             17-18: 10, // Individual Features (Clustered if-necessary)
             },
    */

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
        var mapBounds = this.getMapBounds();
        if (mapBounds !== null && ((options && options.force) ||
          (this.layer.visibility && this.layer.calculateInRange() && this.invalidBounds(mapBounds)))) {
            this.calculateBounds(mapBounds);
            this.resolution = this.layer.map.getResolution(); 
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
        if (this.response && !(options && options.noAbort === true)) {
            this.layer.protocol.abort(this.response);
            this.layer.events.triggerEvent("loadend");
        }
        var evt = {filter: this.createFilter()};
        this.layer.events.triggerEvent("loadstart", evt);
        this.response = this.layer.protocol.read(
            OpenLayers.Util.applyDefaults({
                filter: evt.filter,
                callback: this.merge,
                params: {level: 'L1'},
                scope: this
        }, options));
    },
 
    CLASS_NAME: "OpenLayers.Strategy.ZoomBBOX" 
});
