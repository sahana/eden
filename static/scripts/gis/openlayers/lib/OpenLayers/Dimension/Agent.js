/* Copyright (c) 2006-2011 by OpenLayers Contributors (see authors.txt for
* full list of contributors). Published under the Clear BSD license.
* See http://svn.openlayers.org/trunk/openlayers/license.txt for the
* full text of the license. */


/**
 * @requires OpenLayers/Control/DimensionManager.js
 * @requires OpenLayers/Dimension/Model.js
 */

if(!OpenLayers.Dimension) {
    OpenLayers.Dimension = {};
}
/**
 * Class: OpenLayers.Dimension.Agent
 * Class to display and animate layers across dimension.
 * This class is created by {OpenLayers.Control.DimensionManager} instances
 *
 * Inherits From:
 *  - <OpenLayers.Class>
 */
OpenLayers.Dimension.Agent = OpenLayers.Class({
    /**
     * APIProperty: dimensionManager
     * {<OpenLayers.Control.DimensionManager>}
     */
    dimensionManager : null,
    /**
     * APIProperty: dimension
     * {String}
     */
    dimension: null,
    /**
     * APIProperty: model
     * {OpenLayers.Dimension.Model} defaults to dimensionManager's model, if available
     */
    model: null,
    /**
     * Property: canTick
     * {Boolean}
     */
    canTick : true,
    /**
     * Property: values
     * {Array(Number)}
     */
    values : null,
    /**
     * Property: range
     * {Array(Date)}
     */
    range : null,
    /**
     * Property: layers
     * {Array(<OpenLayers.Layer>)}
     */
    layers : null,
    /**
     * APIProperty: tickMode
     * {String} This property will control if and how the animation dimension is
     *     translated into a dimension range to display on each tick
     *     Must be one of:
     *      "track" - only use single value dimension parameters (Default)
     *      "range" - use a value range for dimension parameters
     *      "cumulative" - use a range from the start value to the current value
     */
    tickMode : "track",
    /**
     * APIProperty: rangeInterval
     * {Number} Value to add or subtract from the current value to build
     *      a dimension range to display with each tick.
     *      ONLY used if tickMode is 'range'
     */
    rangeInterval : 0,
    /**
     * Constructor: OpenLayers.Dimension.Agent
     * Create a new dimension agent to control display of dimensional layers.
     *
     * Parameters:
     * options - {Object} Optional object whose properties will be set on the
     *     control.
     */
    initialize : function(options) {

        OpenLayers.Util.extend(this, options);

        this.events = new OpenLayers.Events(this, null);

        if(this.eventListeners instanceof Object) {
            this.events.on(this.eventListeners);
        }
        if(this.dimensionManager){
            if(!this.dimension){ this.dimension = this.dimensionManager.dimension; }
            if(!this.model){
                this.model = this.dimensionManager.model ||
                    new OpenLayers.Dimension.Model({
                        layers: this.layers,
                        dimension: this.dimension
                    });
            }
        } else if(!this.model && this.layers) {
            this.model = new OpenLayers.Dimension.Model({
                dimension: this.dimension,
                layers: this.layers
            });
        }
        if(this.layers) {
            var dimensionConfig = this.buildRangeAndValues(this.layers);
            this.range = dimensionConfig.range;
            this.values = dimensionConfig.values;
            for(var i=0; i<this.layers.length; i++){
                var layer = this.layers[i];
                layer.calculateInRange = OpenLayers.Function.bind(this.calculateLayerInRange, this, layer);
            }
        }
    },

    destroy : function() {
        this.events.destroy();
        this.dimensionManager.events.unregister('tick', this, this.onTick);
        this.dimensionManager = this.model = this.layers = this.range = this.values = null;
    },

    onTick : function() {
        //Implemented By Subclasses
    },

    addLayer : function(layer) {
        //ensure layer has been processed correctly
        if(!layer.metadata[this.dimension + 'Info'] && layer.dimensions && layer.dimensions[this.dimension]){
            layer.metadata[this.dimension + 'Info'] = this.model.processDimensionValues(layer.dimensions[this.dimension]);
        } else if (!(layer.metadata[this.dimension + 'Info'] || (layer.dimensions && layer.dimensions[this.dimension]))){
            //can't handle a non-dimensional layer
            return false;
        }
        this.layers = (!this.layers) ? [layer] : this.layers.concat(layer);
        //check if it's inclusion effects anything
        var lyrRange = layer.metadata[this.dimension + 'Info'].range;
        var lyrValues = layer.metadata[this.dimension + 'Info'].values;
        if(lyrValues){
            var config = this.buildRangeAndValues(this.layers);
            OpenLayers.Util.extend(this,config);
        } else if(lyrRange[0]<this.range[0] || lyrRange[1]>lyrRange[1]){
            if(lyrRange[1] > this.range[1]) {
                this.range[1] = lyrRange[1];
            }
            if(lyrRange[0] < this.range[0]) {
                this.range[0] = lyrRange[0];
            }
        }
        //modify the layer's calculateInRange function
        layer.calculateInRange = OpenLayers.Function.bind(this.calculateLayerInRange, this, layer);
    },

    removeLayer : function(layer) {
        for(var i = 0, len = this.layers.length; i < len; i++) {
            if(layer == this.layers[i]) {
                this.layers.splice(i, 1);
                if(this.layers.length){
                    var lyrRange = layer.metadata[this.dimension + 'Info'];
                    //if layer was at the edge then adjust dimension model
                    if(lyrRange.min == this.range.min || lyrRange.max == this.range.max){
                        var config = this.buildRangeAndValues(this.layers);
                        this.range = config.range;
                        this.values = config.values;
                    }
                } else {
                    //if we have no more layers then nullify the layers
                    //and dimensional model
                    this.range = this.values = this.layers = null;
                }
                break;
            }
        }
    },

    buildRangeAndValues : function(layers) {
        var info, dimLyrs = [];
        layers = layers || this.layers || this.model.layers;
        var model = this.model || new OpenLayers.Dimension.Model({dimension:this.dimension, 'layers': layers});
        for(var i = 0, len = layers.length; i < len; i++) {
            var lyr = layers[i];
            var dimInfo = (lyr.metadata && lyr.metadata[this.dimension+'Info']) ? lyr.metadata[this.dimension+'Info'] : null;
            if(!dimInfo && lyr.dimensions && lyr.dimensions[this.dimension]) {
                dimInfo = this.model.processDimensionValues(lyr.dimensions[this.dimension]);
                lyr.metadata[this.dimension+'Info'] = OpenLayers.Util.extend({}, dimInfo);
            }
            if(dimInfo){ dimLyrs.push(lyr); }
        }
        if(!dimLyrs.length){
            return {};
        } else {
            info = {
                range: model.calculateRange(dimLyrs),
                values: model.calculateValues(dimLyrs),
                resolution: model.getMaximumResolution(dimLyrs).resolution
            };
            if(!info.values.length){ info.values = null; }
            return info;
        }
    },

    calculateLayerInRange: function(layer){
        var inRange = OpenLayers.Layer.prototype.calculateInRange.call(layer);
        if(inRange){
            var value = this.currentValue || this.dimensionManager.currentValue;
            if(value || value === 0){
                var dimInfo = layer.metadata[this.dimension + "Info"];
                var range = dimInfo.range;
                if(value<range[0] || value>range[1]){
                    inRange = false;
                }
            }
        }
        return inRange;
    },

    CLASS_NAME : 'OpenLayers.Dimension.Agent'
});
