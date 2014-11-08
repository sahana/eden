/* Copyright (c) 2006-2011 by OpenLayers Contributors (see authors.txt for
* full list of contributors). Published under the Clear BSD license.
* See http://svn.openlayers.org/trunk/openlayers/license.txt for the
* full text of the license. */


/**
 * @requires OpenLayers/BaseTypes.js
 * @requires OpenLayers/BaseTypes/Class.js
 * @requires OpenLayers/BaseTypes/Date.js
 * @requires OpenLayers/Control/DimensionManager.js
 */

if(!OpenLayers.Dimension) {
    OpenLayers.Dimension = {};
}

OpenLayers.Dimension.Model = OpenLayers.Class({

    /**
     * Constant: EVENT_TYPES
     *
     * Supported event types:
     *  - *rangemodified* Triggered when layers are added or removed which
     *      affect the range of values available.
     *  - *listmodified* Triggered when layers are added or removed which
     *      affect the list of values available.
     */
    EVENT_TYPES : [
        "rangemodified", 
        "valuesmodified", 
        "resolutionmodified", 
        "addlayer", 
        "removelayer"
    ],

    layers: null,

    dimension: null,

    map: null,

    syncToMap: true,

    values:null,

    range:null,

    initialize: function(options) {
        this.events = new OpenLayers.Events(this, null);
        options = options || {};
        this.dimension = options.dimension;
        if (options.eventListeners instanceof Object) {
            this.events.on(options.eventListeners);
        }
        if (options.map){
            this.setMap(options.map);
        } else if (options.layers) {
            this.setLayers(options.layers);
        } else if (options.range || options.values) {
            if (options.values) {
                this.values = options.values;
                this.range = [this.values[0],this.values[this.values.length-1]];
                //seed the listCache
                this.valueCache = {};
                this.combineLists(this.values);
            } else {
                this.range = options.range;
            }
        }

        //ensure that no processed option is passed to the extend function
        delete options.eventListeners;
        delete options.map;
        delete options.layers;
        delete options.range;
        delete options.values;

        OpenLayers.Util.extend(this, options);
    },
    setMap: function(map) {
        this.map = map;
        if(this.syncToMap){
            this.setLayers(this.map.layers.slice(0));
            this.map.events.on({
                'addlayer': this.onMapAddLayer,
                'removelayer': this.onMapRemoveLayer,
                scope: this
            });
        }
    },
    setLayers: function(layers){
        this.layers = [];
        layers = layers || [];
        this.valueCache = this.range = this.listValues = null;
        for (var i=0, len=layers.length; i<len; i++) {
            this.addLayer(layers[i]);
        }
        if (!this.layers.length) {
            this.layers = null;
        }
    },

    addLayer: function(layer) {
        if(layer.dimensions && layer.dimensions[this.dimension]) {
            var dim = layer.dimensions[this.dimension];
            var dimConfig = this.processDimensionValues(dim);
            layer.metadata[this.dimension + 'Info'] = OpenLayers.Util.extend({}, dimConfig);
            if (!this.layers) { 
                this.layers = []; 
            }
            this.layers.push(layer);
            this.combineDimensionInfo(dimConfig);
            this.events.triggerEvent('addlayer',{
                object: this.map || layer.map,
                layer: layer
            });
        }
    },
    removeLayer: function(layer) {
        if(layer.metadata[this.dimension + 'Info']) {
            var ndx = OpenLayers.Util.indexOf(this.layers,layer);
            this.layers.splice(ndx,1);
            if (this.layers.length) {
                var info = layer.metadata[this.dimension + 'Info'];
                this.removeDimensionInfo(info);
            }
            this.events.triggerEvent('removelayer',{
                object: this.map || layer.map,
                layer: layer
            });
        }
    },
    onMapAddLayer: function(evt){
        this.addLayer(evt.layer);
    },
    onMapRemoveLayer: function(evt){
        this.removeLayer(evt.layer);
    },
    processDimensionValues: function(dim) {
        var range = [Number.MAX_VALUE,-1*Number.MAX_VALUE], valList = [], resolution;
        var values = dim.values || [], nval;
        for (var i = 0, ii = values.length; i < ii; ++i) {
            if (typeof(values[i])=='string' && values[i].indexOf("/")>-1) {
                var valueParts = values[i].split("/");
                if(valueParts.length > 1) {
                    for (var j=0,jj=valueParts.length;j<jj;++j) {
                        if (this.dimension=='time') {
                            var val = valueParts[j];
                            nval = OpenLayers.Date.parse(val).getTime();
                            if (!nval) { 
                                nval = new Date(val).getTime(); 
                            }
                            if (!nval) { 
                                nval = val; 
                            }
                            valueParts[j] = nval;
                        } else if (+valueParts[j] || +valueParts[j]===0) {
                            valueParts[j] = parseFloat(valueParts[j]);
                        }
                    }
                    var min = valueParts[0], max = valueParts[1], res = valueParts[2];

                    //TODO Handle array of interval/res values
                    if (min<range[0]) { 
                        range[0] = min; 
                    }
                    if (max>range[1]) { 
                        range[1] = max; 
                    }
                    //TODO Handle various resolution values
                    if (!resolution) { 
                        resolution = res; 
                    }
                }
            } else {
                var v = values[i];
                if (this.dimension == 'time') {
                    nval = OpenLayers.Date.parse(v).getTime();
                    if (!nval) { 
                        nval = new Date(v).getTime(); 
                    }
                    if (!nval) { 
                        nval = v; 
                    }
                    v = nval;
                } else if (typeof(v)=='string' && (+v || +v === 0)) {
                    v = parseFloat(v);
                }
                if (v < range[0]) { 
                    range[0]=v; 
                }
                if (v > range[1]) { 
                    range[1]=v; 
                }
                valList[valList.length] = v;
            }
        }
        var retObj = {
            'range': range,
            'resolution': resolution,
            'values': valList.length ? valList : null
        };
        if (this.dimension == 'time' && retObj.resolution) {
            var timeRes = this.parseISOPeriod(retObj.resolution);
            OpenLayers.Util.extend(retObj, timeRes);
        }
        return retObj;
    },
    combineDimensionInfo: function(info) {
        var rangeMod = valMod = resMod = false;
        var origRes, origRange, origValues;
        // check range and adjust and fire event as needed
        origRange = this.range && this.range.slice();
        if (!this.range) { 
            this.range = [Number.MAX_VALUE, -1*Number.MAX_VALUE]; 
        }
        if (info.range[0]<this.range[0]) {
            this.range[0] = info.range[0];
            rangeMod = true;
        }
        if (info.range[1]>this.range[1]) {
            this.range[1] = info.range[1];
            rangeMod = true;
        }
        //check values list, combine, and fire event as needed
        if (info.values) {
            var len = this.values && this.values.length;
            origValues = this.values && this.values.slice();

            if (!this.valueCache) {
                this.valueCache = {};
                this.values = this.combineLists(this.values || [], info.values, this.valueCache);
            } else {
                this.values = this.combineLists(info.values, null, this.valueCache);
            }

            if (this.values.length != len) {
                valMod = true;
            }
        }
        if (info.resolution) {
            // TODO - What about various resolution values (fire event?)
            // using the smallest resolution
            origRes = this.resolution;
            if (this.resolution) {
                if (info.resolution != this.resolution) {
                    resMod = true;
                    if (info.resolution<this.resolution) {
                        this.resolution = info.resolution;
                    }
                }
            } else {
                resMod = true;
                this.resolution = info.resolution;
            }
        }

        if (rangeMod) {
            this.events.triggerEvent('rangemodified', {
                range: this.range,
                prevRange: origRange
            });
        }
        if (valMod) {
            this.events.triggerEvent('valuesmodified', {
                values: this.values,
                prevValues: origValues
            });
        }
        if (resMod) {
            this.events.triggerEvent('resolutionmodified', {
                resolution: this.resolution,
                prevResolution: origRes,
                modelModified: this.resolution != origRes
            });
        }
    },
    removeDimensionInfo: function(info) {
        var rangeMod = valMod = resMod = false;
        var origRange = range = this.range || [Number.MAX_VALUE,-1*Number.MAX_VALUE];
        var origRes = this.resolution;
        var origValues = this.values;
        if (info.values) {
            var len = this.values.length;
            this.values = this.removeListValues(info.values, this.valueCache);
            if (this.values.length<len) {
                valMod = true;
                if (info.values[0]<this.values[0]) {
                    rangeMod = true;
                    range[0] = this.values[0];
                }
                if (info.values.slice(-1).pop()>this.values.slice(-1).pop()) {
                    rangeMod = true;
                    range[1] = this.values.slice(-1).pop();
                }
            }
            this.range = range;
        } else {
            if (info.range[0] == range[0] || info.range[1] == range[1]) {
                var min = range[0], max = range[1];
                this.range = this.calculateRange();
                if (this.range[0] !== min || this.range[1] !== max) {
                    rangeMod = true;
                }
            }
        }
        if (info.resolution) {
            if (info.resolution == this.resolution) {
                this.resolution = this.getMaximumResolution().resolution;
                if (origRes != this.resolution) {
                    resMod = true;
                }
            }
        }
        if (rangeMod) {
            this.events.triggerEvent('rangemodified', {
                range: this.range,
                prevRange: origRange
            });
        }
        if (valMod) {
            this.events.triggerEvent('valuesmodified', {
                values: this.values,
                prevValues: origValues
            });
        }
        if (resMod) {
            this.events.triggerEvent('resolutionmodified', {
                resolution: this.resolution,
                prevResolution: origRes,
                modelModifed: true
            });
        }
    },
    combineLists: function(list1, list2, listCache) {
        var cache = (listCache === false) ? {} : listCache || this.valueCache || {};
        var arr = [];
        var process = function(list){
            for (var i = 0, len = list.length; i < len; i++) {
                var val = list[i];
                if (cache[val]) {
                    ++cache[val];
                } else {
                    cache[val]=1;
                }
            }
        };
        process(list1);

        if (list2) { 
            process(list2); 
        }

        for (var k in cache) {
            if (cache.hasOwnProperty(k) && cache[k]>0) {
                arr[arr.length] = +k;
            }
        }
        arr.sort(function(a,b) {
            return a-b;
        });
        return arr;
    },
    removeListValues: function(values, valueCache){
        var cache = (valueCache === false) ? false : valueCache || this.valueCache;
        if (!cache) {
            return values;
        } else {
            var arr = [];
            for (var i = 0, len = values.length; i < len; i++) {
                var val = values[i];
                if (cache[val]) {
                    if (--cache[val] === 0) {
                        delete cache[val];
                    }
                }
            }
            for (var k in cache) {
                if (cache.hasOwnProperty(k) && cache[k]>0) {
                    arr[arr.length] = +k;
                }
            }
            return arr;
        }
    },
    getMinimumResolution: function(layers){
        layers = layers || this.layers;
        var minRes = Number.MAX_VALUE,
        unit, step;
        for (var i=0,len=layers.length;i<len;++i) {
            var info = layers[i].metadata[this.dimension + 'Info'];
            var res = info.resolution;
            if (res < minRes) {
                minRes = res;
                unit = info.timeUnits;
                step = info.timeStep;
            }
        }
        return {
            resolution : minRes,
            timeStep : step ? step : undefined,
            timeUnits : unit ? unit : undefined
        };
    },
    getMaximumResolution: function(layers){
        layers = layers || this.layers;
        var maxRes = -1 * Number.MAX_VALUE,
        unit, step;
        for (var i=0,len=layers.length;i<len;++i) {
            var info = layers[i].metadata[this.dimension + 'Info'];
            var res = info.resolution;
            if (res > maxRes) {
                maxRes = res;
                unit = info.timeUnits;
                step = info.timeStep;
            }
        }
        return {
            resolution : maxRes,
            timeStep : step ? step : undefined,
            timeUnits : unit ? unit : undefined
        };
    },
    getLowestCommonResolution: function(layers){
        //TODO - implement
        /**
        layers = layers || this.layers;
        var res = layers[0].metadata[this.dimension + 'Info'].resolution;
        if(layers.length === 1){
            return res;
        } else {
            for(var i=1,len=layers.length;i<len;++i){
                var nextRes = layers[i].metadata[this.dimension + 'Info'].resolution;

            }
        }
        **/
    },
    getHighestCommonResolution: function(layers){
        //TODO - implement
        /**
        layers = layers || this.layers;
        var res = layers[0].metadata[this.dimension + 'Info'].resolution;
        if(layers.length === 1){
            return res;
        } else {
            for(var i=1,len=layers.length;i<len;++i){
                var nextRes = layers[i].metadata[this.dimension + 'Info'].resolution;

            }
        }
        **/
    },
    calculateRange: function(layers){
        layers = layers || this.layers;
        var range = layers[0].metadata[this.dimension + 'Info'].range;
        if (layers.length === 1) {
            return range;
        } else {
            for (var i=1,len=layers.length;i<len;++i) {
                var nextRange = layers[i].metadata[this.dimension + 'Info'].range;
                if (nextRange[0]<range[0]) {
                    range[0] = nextRange[0];
                }
                if (nextRange[1]>range[1]) {
                    range[1] = nextRange[1];
                }
            }
            return range;
        }
    },
    calculateValues: function(layers){
        layers = layers || this.layers;
        var values = layers[0].metadata[this.dimension + 'Info'].values;
        if (layers.length === 1) {
            return (values) ? values : [];
        } else {
            var cache = {};
            values = this.combineLists(
                values || [], 
                layers[1].metadata[this.dimension + 'Info'].values || [], 
                cache
            );
            for (var i=2,len=layers.length;i<len;++i) {
                values = this.combineLists(
                    layers[i].metadata[this.dimension + 'Info'].values || [], 
                    null, 
                    cache
                );
            }
            return values;
        }
    },
    parseISOPeriod : function(period) {
        var periodRE = [/(\d+)Y/, /(\d+)M/, /(\d+)D/, /(\d+)H/, /(\d+)M/, /(\d+)S/],
        periods = period.split('P')[1].split('T'),
        resolution, d = {days:0};
        if (periods[0]) {
            var dt = periods[0];
            d.years = periodRE[0].test(dt) ? +(dt.match(periodRE[0])[1]) : 0;
            d.months = (periodRE[1].test(dt) ? +(dt.match(periodRE[1])[1]) : 0) + (12 * d.years);
            d.days = (periodRE[2].test(dt) ? +(dt.match(periodRE[2])[1]) : 0) + (30.5 * d.months);
        }
        if (periods[1]) {
            var tm = periods[1];
            d.hours = (periodRE[3].test(tm) ? +(tm.match(periodRE[3])[1]) : 0) + (24 * d.days);
            d.minutes = (periodRE[4].test(tm) ? +(tm.match(periodRE[4])[1]) : 0) + (60 * d.hours);
            d.seconds = (periodRE[5].test(tm) ? +(tm.match(periodRE[5])[1]) : 0) + (60 * d.minutes);
        }
        var unitTest = ['seconds', 'minutes', 'hours', 'days', 'months', 'years'];
        for (var i = 0, j = 5; i < unitTest.length; ++i, --j) {
            var u = unitTest[i];
            var s = periodRE[j];
            if (j>2 && s.test(tm) || j<3 && s.test(dt)) {
                resolution = {
                    timeStep : d[u],
                    timeUnits : OpenLayers.TimeUnit[u.toUpperCase()]
                };
                break;
            }
        }
        if (resolution) {
            resolution.resolution = OpenLayers.TimeStep[resolution.timeUnits] * resolution.timeStep;
        }
        return resolution;
    },

    guessPlaybackRate: function(){
        var values = this.calculateValues(),
        range = this.calculateRange(),
        info = this.getMaximumResolution(),
        retObj = {};
        if (values && values.length) {
            retObj.snapToList = true;
            return retObj;
        } else if (info && info.resolution) {
            retObj.step = info.resolution;
            if (this.dimension == 'time') {
                retObj.timeStep = info.timeStep;
                retObj.timeUnits = info.timeUnits;
            }
        }
        return retObj;
    }
});

OpenLayers.TimeUnit = {
    SECONDS:'Seconds',
    MINUTES:'Minutes',
    HOURS:'Hours',
    DAYS:'Date',
    MONTHS:'Month',
    YEARS:'FullYear'
};

OpenLayers.TimeStep = {};
OpenLayers.TimeStep[OpenLayers.TimeUnit.SECONDS] = 1000;
OpenLayers.TimeStep[OpenLayers.TimeUnit.MINUTES] = 6.0e4;
OpenLayers.TimeStep[OpenLayers.TimeUnit.HOURS] = 3.6e6;
OpenLayers.TimeStep[OpenLayers.TimeUnit.DAYS] = 8.64e7;
OpenLayers.TimeStep[OpenLayers.TimeUnit.MONTHS] = 3.15576e10 / 12;
OpenLayers.TimeStep[OpenLayers.TimeUnit.YEARS] = 3.15576e10;

//Adjust the OpenLayers date parse regex to handle BCE dates & years longer than 4 digits
OpenLayers.Date.dateRegEx =
    /^(?:(-?\d+)(?:-(\d{2})(?:-(\d{2}))?)?)?(?:(?:T(\d{1,2}):(\d{2}):(\d{2}(?:\.\d+)?)(Z|(?:[+-]\d{1,2}(?::(\d{2}))?)))|Z)?$/;
