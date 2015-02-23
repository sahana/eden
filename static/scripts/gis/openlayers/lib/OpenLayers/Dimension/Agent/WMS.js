/* Copyright (c) 2006-2011 by OpenLayers Contributors (see authors.txt for
* full list of contributors). Published under the Clear BSD license.
* See http://svn.openlayers.org/trunk/openlayers/license.txt for the
* full text of the license. */


/**
 * @requires OpenLayers/BaseTypes.js
 * @requires OpenLayers/BaseTypes/Class.js
 * @requires OpenLayers/BaseTypes/Date.js
 * @requires OpenLayers/Dimension/Agent.js
 */

/**
 * Class: OpenLayers.Dimension.Agent.WMS
 * Class to display and animate WMS layers across dimensions.
 * This class is created by {OpenLayers.Control.DimensionManager} instances
 *
 * Inherits From:
 *  - <OpenLayers.Dimension.Agent>
 */
OpenLayers.Dimension.Agent.WMS = OpenLayers.Class(OpenLayers.Dimension.Agent, {
    /**
     * APIProperty: intervalMode
     * {String} If a wms layer has distinct valid dimension intervals,
     *     then this property will control if and how the animation value is
     *     translated into a valid value for the layer
     *     Must be one of:
     *     "lastValid" - continue to display it using the last valid time within
     *         the overall control time range
     *     "nearest" - (Default) use the nearest valid time within the overall
     *         control time range.
     *     "exact" - only display the layer when there's an exact match (to the
     *         grainularity of the step unit) in the control time and an interval
     */
    intervalMode : 'nearest',

    /**
     * APIProperty: maxErrors
     * {Integer} Maximum number of consecutive errors wrt tile loading before 
     *     prebufferring is cancelled. Defaults to 5.
     */
    maxErrors: 5,

    /**
     * Constructor: OpenLayers.Control.DimensionManager.WMS
     * Create a new Dimension manager control for temporal WMS layers.
     *
     * Parameters:
     * options - {Object} Optional object whose properties will be set on the
     *     control.
     */
    initialize : function(options) {
        OpenLayers.Dimension.Agent.prototype.initialize.call(this, options);
        //add layer loadend listeners
        if(this.layers) {
            for(var i = 0, len = this.layers.length; i < len; i++) {
                this.layers[i].events.on({
                    'loadend' : this.onLayerLoadEnd,
                    'loadstart' : this.onLayerLoadStart,
                    scope : this
                });
            }
        }
    },

    shouldPrebuffer: function() {
        // never prebuffer in the composer
        if (window.location.href.match(/view|new/)===null) {
            if (this.dimensionManager.prebuffer !== null) {
                return this.dimensionManager.prebuffer;
            } else {
                return OpenLayers.Util.getParameters().prebuffer === "true";
            }
        }
    },

    prebuffer: function() {
        this.count = 0;
        if (this.layers && this.shouldPrebuffer()) {
            for (var i=0, ii=this.layers.length; i<ii; ++i) {
                var layer = this.layers[i];
                this.preBufferLayer(layer);
            }
        }
    },

    getNumberOfSteps: function() {
        var steps = 0;
        if (this.layers) {
            if (this.model.values) {
                steps = this.layers.length * this.model.values.length;
            } else if (this.model.resolution) {
                steps = this.layers.length * ((this.model.range[1] - this.model.range[0])/this.model.resolution);
            }
        }
        return steps;
    },

    preBufferLayer: function(layer) {
        var div = document.createElement("div");
        document.body.appendChild(div);
        var size = layer.map.size;
        div.style.width = size.w + "px";
        div.style.height = size.h + "px";
        div.style.top = "-5000px";
        div.style.left = "-5000px";
        div.style.position = "absolute";
        var map = this.createOffscreenMap(layer.map, div);
        var clone = layer.clone();
        clone.calculateInRange = OpenLayers.Layer.prototype.calculateInRange;
        map.addLayer(clone);
        map.setCenter(layer.map.getCenter(), layer.map.getZoom());
        var i=0, len;
        var stepsPerLayer = this.getNumberOfSteps() / this.layers.length;
        var maxFrames = null;
        if (this.dimensionManager.maxframes !== null) {
            maxFrames = this.dimensionManager.maxframes;
        } else if (OpenLayers.Util.getParameters().maxframes !== undefined) {
            maxFrames = parseInt(OpenLayers.Util.getParameters().maxframes, 10);
        }
        if (maxFrames !== null) {
            len = Math.min(stepsPerLayer, maxFrames);
        } else {
            len = stepsPerLayer;
        }
        this._errorCount = 0;
        clone.events.on({
            'tileloaded': function() {
                this._errorCount = 0;
            },
            'tileerror': function() {
                this._errorCount++;
            },
            'loadend': function() {
                i++;
                if (i<len && this._errorCount < this.maxErrors) {
                    this.doBufferStep(clone, i);
                } else {
                    // we are done, clean up
                    map.destroy();
                    document.body.removeChild(div);
                }
            },
            scope: this
        });
        this.doBufferStep(clone, 0);
    },

    doBufferStep: function(clone, i) {
        this.dimensionManager.counter++;
        var value = null;
        if (this.model.values) {
            value = this.model.values[i];
        } else if (this.model.resolution) {
            value = this.model.range[0] + (this.model.resolution*i);
        }
        // trigger on the dimensionManager since the model sometimes is
        // a plain object
        if (this.dimensionManager.triggerPrebuffer() !== false) {
            if (value !== null) {
                this.requestTime(clone, value);
            }
        }
    },

    createOffscreenMap: function(map, div) {
        var options = OpenLayers.Util.applyDefaults({}, map.options);
        delete options.controls;
        options.div = div;
        var newMap = new OpenLayers.Map(options);
        map.tileManager.addMap(newMap);
        return newMap;
    },

    addLayer : function(layer) {
        layer.events.on({
            'loadend' : this.onLayerLoadEnd,
            'loadstart' : this.onLayerLoadStart,
            scope : this
        });
        OpenLayers.Dimension.Agent.prototype.addLayer.call(this, layer);
    },

    removeLayer : function(layer) {
        layer.events.un({
            'loadend' : this.onLayerLoadEnd,
            'loadstart' : this.onLayerLoadStart,
            scope : this
        });
        OpenLayers.Dimension.Agent.prototype.removeLayer.call(this, layer);
    },

    destroy : function() {
        if(this.layers && this.layers.length){
            for(var i = this.layers.length - 1; i > -1; i--) {
                this.removeLayer(this.layers[i]);
            }
        }
        OpenLayers.Dimension.Agent.prototype.destroy.call(this);
    },

    onTick : function(evt) {
        var i, ii;
        this.currentValue = evt.currentValue || this.dimensionManager.currentValue;

        var inrange = this.currentValue <= this.range[1] && this.currentValue >= this.range[0];
        //this is an inrange flag for all the entire value range of layers managed by
        //this dimension agent and not a specific layer
        if(inrange) {
            var validLayers = OpenLayers.Array.filter(this.layers, function(lyr) {
                return lyr.visibility && lyr.calculateInRange();
            });            
            this.loadQueue = validLayers.length;

            this.canTick = !this.loadQueue;

            for(i=0, ii=this.layers.length; i<ii; i++){
                this.applyDimension(this.layers[i], this.currentValue);
            }
        } else {
            //the dimension manager fired a tick with a value outside of the full data range of this agent
            //we want to turn off the display of layers but not change their visibility
            //normally this would be taken care of the map's moveTo function, but the map is not moving
            //in space, only in time or other non XY dimension.
            for(i=0, ii=this.layers.length; i<ii; i++){
                //copied from parts of Map::moveTo section preceeding the ...triggerEvent("move") call
                var layer = this.layers[i];
                var inRange = layer.calculateInRange();
                if (layer.inRange != inRange || !inRange && layer.div.style.display != "none") {
                    // the inRange property has changed. If the layer is
                    // no longer in range, we turn it off right away. If
                    // any layer was possiblly in range, the applyDimension
                    // call above would turn on the layer.
                    layer.inRange = inRange;
                    if (!inRange) {
                        layer.display(false);
                    }
                    if(layer.map){
                        layer.map.events.triggerEvent("changelayer", {
                            layer: layer, property: "visibility"
                        });    
                    }
                }
            }
        }
    },

    applyDimension : function(layer, value) {
        var minValue;
        if(this.tickMode == 'range'){
            minValue = value - this.rangeInterval;
        } 
        else if (this.tickMode == 'cumulative'){
            minValue = this.range[0];
        } else {
            //tickMode is 'track'
            if(this.dimensionManager.snapToList && layer.metadata[this.dimension+'Info'].list){
                //find where this value fits into
                var list = layer.metadata[this.dimension+'Info'].list;
                var match = this.findNearestValues(value, list);
                if(!match){
                        value = null;
                } else if(match.exact == -1){
                    if(this.intervalMode == 'lastValid'){
                        value = (match.before > -1) ? list[match.before] : list[0];
                    } else if(this.intervalMode == 'nearest'){
                        var before = (match.before > -1) ? match.before : 0;
                        var after = (match.after >-1) ? match.after : list.length-1;
                        if(Math.abs(value - list[before]) >= Math.abs(value - list[after])){
                            value = list[after];
                        } else {
                            value = list[before];
                        }
                    } else if(this.intervalMode == 'exact'){
                        value = null;
                    }
                }
                //value remains same if the match is exact regardless of intervalMode
            }
        }
        if(!value){
            this.onLayerLoadEnd();
        } else {
            //actually convert minValue & value into a new request
            var titleDim = this.dimension.substr(0,1).toUpperCase()+this.dimension.substr(1);
            if(this['request'+titleDim]){
                this['request'+titleDim](layer,value,minValue);
            } else {
                this.requestValue(layer,value,minValue,titleDim);
            }
        }
    },
    requestTime: function(layer, time, minTime){
        var pad = OpenLayers.Number.zeroPad;
        var param = {
            time:''
        };
        var truncDate = function(date, unit){
            return date['getUTC'+unit]();
        };
        var buildDateString = function(date, unit){
            var str = OpenLayers.Date.toISOString(date);
            if(str != "Invalid Date"){
                switch(unit){
                    case OpenLayers.TimeUnit.YEARS:
                        str = str.split('-')[0];
                        break;
                    case OpenLayers.TimeUnit.MONTHS:
                        str = str.split('-').slice(0,2).join('-');
                        break;
                    case OpenLayers.TimeUnit.DAYS:
                        str = str.split('T')[0];
                        break;
                    case OpenLayers.TimeUnit.HOURS:
                        str = str.split(':')[0] + ':00Z';
                        break;
                }
            }
            return str;
        };
        var units = this.dimensionManager.timeUnits;
        if(minTime){
            param.time += buildDateString(new Date(minTime), units) + '/';
        }
        param.time += buildDateString(new Date(time), units);
        layer.mergeNewParams(param);
    },
    requestElevation: function(layer, elev, minElev){
        var param = {
            elevation: (minElev) ? minElev + '/' + elev : elev
        };
        layer.mergeNewParams(param);
    },
    requestValue: function(layer, val, minVal, dimName){
        var param = {};
        var reqVal = (minVal) ? minVal + '/' + val : val;
        param['dim'+dimName] = reqVal;
        layer.mergeNewParams(param);
    },

    /**
     *
     * @param {Object} testValue
     * @param {Array[{Numbers}]} MUST be a sorted value array
     */
    findNearestValues : function(testValue, values) {
        return OpenLayers.Control.DimensionManager.findNearestValues(testValue,values);
    },

    onLayerLoadEnd : function() {
        --this.loadQueue;
        if(this.loadQueue <= 0) {
            this.canTick = true;
        }
    },

    CLASS_NAME : 'OpenLayers.Dimension.Agent.WMS'
});
