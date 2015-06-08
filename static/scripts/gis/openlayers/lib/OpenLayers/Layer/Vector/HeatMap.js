/* Copyright (c) 2006-2008 MetaCarta, Inc., published under the Clear BSD
 * license.  See http://svn.openlayers.org/trunk/openlayers/license.txt for the
 * full text of the license. */

/**
 * @requires OpenLayers/Layer/Vector.js
 * @requires OpenLayers/Geometry/Point.js
 * @requires OpenLayers/Renderer/CanvasHeatMap.js
 */

/**
 * Class: OpenLayers.Layer.Vector.HeatMap
 * A special layer type to render point features as heat map on a
 * canvas element.
 *
 * Inherits from:
 *  - <OpenLayers.Layer.Vector>
 */
OpenLayers.Layer.Vector.HeatMap = OpenLayers.Class(OpenLayers.Layer.Vector, {

    /**
     * Constructor: OpenLayers.Layer.Vector.HeatMap
     * Create a new heat map layer
     *
     * Parameters:
     * name - {String} A name for the layer
     * options - {Object} Optional object with non-default properties to set on
     *           the layer.
     *
     * Returns:
     * {<OpenLayers.Layer.Vector.HeatMap>} A new vector layer
     */
    initialize: function(name, options) {
        options.renderers = ["CanvasHeatMap"];
        OpenLayers.Layer.Vector.prototype.initialize.apply(this, arguments);
        
        this.geometryType = OpenLayers.Geometry.Point;
        this.events.addEventType("renderProgress");
              
        // register an event to monitor the heat map generation progress
        this.renderer.onRenderProgress = function(event) {
            // just redirect the event
            this.events.triggerEvent("renderProgress", event);
        };
        this.renderer.events.register("renderProgress", this, this.renderer.onRenderProgress);
    },
    
    destroy: function() {
        this.renderer.events.un({
            "renderProgress": this.renderer.onRenderProgress,
            scope: this
        });
        
        OpenLayers.Layer.Vector.prototype.destroy.apply(this, arguments);
    },

    CLASS_NAME: "OpenLayers.Layer.Vector.HeatMap"
});
