/* Copyright (c) 2006-2011 by OpenLayers Contributors (see authors.txt for
 * full list of contributors). Published under the Clear BSD license.
 * See http://svn.openlayers.org/trunk/openlayers/license.txt for the
 * full text of the license. */

/**
 * @requires OpenLayers/Control.js
 * @requires OpenLayers/Dimension/Model.js
 */

/**
 * Class: OpenLayers.Control.DimensionManager
 * Control to display and animate map layers across a non-geographic dimension (time, elevation, etc..).
 *
 * Inherits From:
 *  - <OpenLayers.Control>
 */
OpenLayers.Control.DimensionManager = OpenLayers.Class(OpenLayers.Control, {

    /**
     * Constant: EVENT_TYPES
     *
     * Supported event types:
     *  - *tick* Triggered when the control advances one step in value.
     *      Listeners receive an event object with a *currentValue* parameter.
     *      Event is fired after the value has been incremented but before the
     *      map or layer display is modified.
     *  - *play* Triggered when the play function is called.
     *      Returning 'false' from this event will prevent the control
     *      from playing the animation.
     *  - *stop* Triggered when the control stops a series animation.
     *      Listeners receive an event object with a {Boolean} *rangeExceeded*
     *      property indicating the control stopped due to reaching the end of
     *      its configured value range (true) or due to the stop function call
     *      (false).
     *  - *rangemodified* Triggered when the control's animationRange is set
     *      programattically.
     *  - *reset* Triggered when the control resets a series animation.
     *      Listeners receive an event object with a {Boolean} *looped*
     *      property indicating the control reset due to running in looped mode
     *      (true) or the reset function call (false)
     *  - *prebuffer* Triggered on each prebuffering step.
     *      Listeners receive an event object with a {Float} *progress*
     *      property indicating the progress of the prebuffering, value ranges
     *      from 0 to 1.
     */
    EVENT_TYPES : ["beforetick", "tick", "play", "stop", "reset", "rangemodified", "prebuffer"],


    /**
     * APIProperty: model
     * {OpenLayers.Dimension.Model}
     */
    model : null,

    /**
     * APIProperty: prebuffer
     * {Boolean}
     */
    prebuffer: null,

    /** APIProperty: maxframes
     * {Integer}
     */
    maxframes: null,

    /**
     * APIProperty: autoSync
     * {Boolean} Automatically adjust the available animationRange and
     *    possibly the currentValue of this control in response to
     *    a 'rangemodified' event from the 'model' (fired when layers
     *    are added or removed from the map and affect the overall range
     *    of valid values)
     */
    autoSync : true,

    /**
     * APIProperty: dimension
     * {String} The dimension this control manages
     *     Examples: 'time', 'elevation'
     */
    dimension : null,

    /**
     * APIProperty: animationRange
     * {Array(Number)} 2 member array containing the minimum and maximum
     *     values that the animation will use. The 1st value should ALWAYS
     *     be less than the second value. Use negative step values to do
     *     reverse stepping. This is separate from the model's range and
     *     should be equal to or a subset of that range.
     */
    animationRange : null,

    /**
     * APIProperty: step
     * {Number} The number of units each tick will advance the current
     *     dimension. Negative units will tick the dimension in reverse.
     *     Default : 1.
     */
    step : 1,

    /**
     * APIProperty: timeUnits
     * {<OpenLayers.TimeUnit>} (Optional) Only used when 'dimension' is 'time'.
     *     The date part the time value will be incremented by. Use of this
     *     property will make time value changes more accurate over a long
     *     period.
     */
    timeUnits: null,

    /**
     * APIProperty: timeStep
     * {Number} (Optional) Only used when 'dimension' is 'time'.
     *     The amount of timeUnits the time value will be incremented by. Use of this
     *     property will make time value changes more accurate over a long
     *     period.
     */
    timeStep: null,

    /**
     * APIProperty: frameRate
     * {Number} A positive floating point number of frames (or ticks) per
     *     second to use in series animations. Values less than 1 will
     *     make each tick last for more than 1 second. Example: 0.5 = 1 tick
     *     every 2 seconds. 3 = 3 ticks per second.
     *     Default : 1.
     */
    frameRate : 1,

    /**
     * APIProperty: loop
     * {Boolean} true to continue running the animation until stop is called
     *     Default:false
     */
    loop : false,

    /**
     * APIProperty: snapToList
     * {Boolean} If valuesList is configured and this property is true then
     *     tick will advance to the next value in the valuesList array
     *     regardless of the step value.
     */
    snapToList : null,

    /**
     * APIProperty: maxFrameDelay
     * {Number} The number of frame counts to delay the firing of the tick event
     *     while the control waits for its dimension agents to be ready to advance.
     *     Default: 1
     */
    maxFrameDelay : 1,

    /**
     * APIProperty: currentValue
     * {Number} The current value of the series animation
     */
    currentValue : null,

    /**
     * Property: agents
     * {Array(<OpenLayers.Dimension.Agent>)} An array of the agents that
     *     this control "manages". Read-Only
     */
    agents : null,

    /**
     * Property: lastValueIndex
     * {Number} The array index of the last value used in the control when
     * snapToList is true.
     */
    lastValueIndex : -1,

    triggerPrebuffer: function() {
        var progress = this.counter / this.totalCount;
        return this.events.triggerEvent("prebuffer", {progress: progress});
    },

    /**
     * Constructor: OpenLayers.Control.DimensionManager
     * Create a new dimension manager control.
     *
     * Parameters:
     * options - {Object} Optional object whose properties will be set on the
     *     control.
     */
    initialize : function(options) {
        options = options || {};
        OpenLayers.Control.prototype.initialize.call(this, options);
        if(this.model){
            this.syncToModel();
        }
        if(this.agents) {
            var i, len, agent;
            this.totalCount = 0;
            for (i=0, len=this.agents.length; i<len; i++) {
                agent = this.agents[i];
                if (agent instanceof OpenLayers.Dimension.Agent.WMS) {
                    this.totalCount += agent.getNumberOfSteps();
                }
            }
            this.counter = 0;
            for(i = 0, len = this.agents.length; i < len; i++) {
                agent = this.agents[i];
                agent.dimensionManager = this;
                // there are two code paths where we need to prebuffer, one is where
                // a control is configured with agents in its config, the other one is
                // where we use buildAgents to build the agents on the fly.
                if (agent instanceof OpenLayers.Dimension.Agent.WMS) {
                    agent.prebuffer();
                }
                this.events.on({
                    'tick' : agent.onTick,
                    scope : agent
                });
            }
        }
        this.events.on({
            'play' : function() {
                if(!this.agents || !this.agents.length) {
                    console.warn("Attempting to play a dimension manager control without any dimensional layers");
                    return false;
                }
            },
            scope : this
        });
    },

    /**
     * APIMethod: destroy
     * Destroys the control
     */
    destroy : function() {
        for(var i = this.agents.length - 1; i > -1; i--) {
            this.agents[i].destroy();
        }
        OpenLayers.Control.prototype.destroy.call(this);
    },

    /**
     * APIMethod: setMap
     * Sets the map parameter of the control. Also called automattically when
     * the control is added to the map.
     * Parameter:
     *    map {<OpenLayers.Map>}
     */
    setMap : function(map) {
        OpenLayers.Control.prototype.setMap.call(this, map);
        //if the control was not directly initialized with a model, then
        //get layers from map and build the model and the dimension agents
        if(!this.model){
            this.model = new OpenLayers.Dimension.Model({
                map:map,
                dimension:this.dimension,
                syncToMap:this.autoSync
            });
        } else {
            //TODO don't recalc model if it is provided, unless autoSync is true
            if(this.model && !(this.model instanceof OpenLayers.Dimension.Model)){
                this.model = new OpenLayers.Dimension.Model(OpenLayers.Util.applyDefaults(this.model,{'map':map}));
            }
        }
        this.syncToModel();
        if(this.autoSync){
            this.model.events.on({
                'rangemodified': this.onModelRangeModified,
                'valuesmodified': this.onModelValuesModified,
                'addlayer': this.onModelLayerAdded,
                'removelayer': this.onModelLayerRemoved,
                scope: this
            });
        }
        if(!this.agents && map.layers.length) {
            this.agents = this.buildAgents(this.model);
            // loop over the agents created with buildAgents if any and prebuffer
            if (this.agents !== null) {
                var i, ii, agent;
                this.totalCount = 0;
                for (i=0, ii=this.agents.length; i<ii; i++) {
                    agent = this.agents[i];
                    if (agent instanceof OpenLayers.Dimension.Agent.WMS) {
                        this.totalCount += agent.getNumberOfSteps();
                    }
                }
                this.counter = 0;
                for (i=0, ii=this.agents.length; i<ii; ++i) {
                    agent = this.agents[i];
                    if (agent instanceof OpenLayers.Dimension.Agent.WMS) {
                        agent.prebuffer();
                    }
                }
            }
        }
        if(this.modelCache && this.modelCache.range && !this.animationRange){
            this.setAnimationRange(this.modelCache.range);
        }
        if(this.animationRange && !this.currentValue){
            this.setCurrentValue(this.animationRange[0]);
        } else if(this.currentValue) {
            this.setCurrentValue(this.currentValue);
        }
    },

    /**
     * Method: tick
     * Advance/reverse dimension values one step forward/backward. Fires the 'tick' event
     * if value can be incremented without exceeding the value range.
     *
     */
    tick : function() {
        var model = this.modelCache;
        if(model.values && this.snapToList) {
            var values = model.values;
            var newIndex = this.lastValueIndex + ((this.step > 0) ? 1 : -1);
            if(newIndex < values.length && newIndex > -1) {
                this.currentValue = values[newIndex];
                this.lastValueIndex = newIndex;
            }
            else {
                //force the currentValue beyond the range
                this.currentValue = (this.step > 0) ? this.animationRange[1] + 100 : this.animationRange[0] - 100;
            }
        }
        else {
            this.incrementValue();
        }
        //test if we have reached the end of our range
        if(this.currentValue > this.model.range[1] || this.currentValue < this.model.range[0]) {
            //loop in looping mode
            if(this.loop) {
                this.clearTimer();
                this.reset(true);
                this.play();
            }
            //stop in normal mode
            else {
                this.clearTimer();
                this._stopped = true;
                this.events.triggerEvent('stop', {
                    'rangeExceeded' : true
                });
            }
        }
        else {
            if(this.canTickCheck()) {
                this.events.triggerEvent('tick', {
                    currentValue : this.currentValue
                });
            }
            else {
                var intervalId, checkCount = 0, maxDelays = this.maxFrameDelay * 4;
                var playing = !!this.timer;
                this.clearTimer();
                intervalId = setInterval(OpenLayers.Function.bind(function() {
                    var doTick = this.canTickCheck() || checkCount++ >= maxDelays;
                    if(doTick) {
                        clearInterval(intervalId);
                        this.events.triggerEvent('tick', {
                            currentValue : this.currentValue
                        });
                        if(!this._stopped && playing){
                            this.clearTimer();
                            this.timer = setInterval(OpenLayers.Function.bind(this.tick, this), 1000 / this.frameRate);
                        }
                    }
                }, this), 1000 / (this.frameRate * 4));
            }
        }
    },

    /**
     * APIMethod: play
     * Begins/resumes the series animation. Fires the 'play' event,
     * then calls 'tick' at the interval set by the frameRate property
     */
    play : function() {
        //ensure that we don't have multiple timers running
        this.clearTimer();
        //start playing
        if(this.events.triggerEvent('play') !== false) {
            delete this._stopped;
            this.tick();
            this.clearTimer(); //no seriously we really really only want 1 timer
            this.timer = setInterval(OpenLayers.Function.bind(this.tick, this), 1000 / this.frameRate);
        }
    },

    /**
     * APIMethod: stop
     * Stops the time-series animation. Fires the 'stop' event.
     */
    stop : function() {
        this.clearTimer();
        this._stopped = true;
        this.events.triggerEvent('stop', {
            'rangeExceeded' : false
        });
    },

    /**
     * APIMethod: setAnimationRange
     * Sets the value range used by this control. Will modify the
     * current value only if the animation is not currently running
     *
     * Parameters:
     * range - {Array(Number)}
     * setTime - {Boolean} false to avoid affecting the currentTime
     *    true to set affect the currentTime even if playback has started
     *    default is undefined. anything other than strictly true or false
     *    will be disregarded.
     */
    setAnimationRange : function(range, setTime) {
        var oldRange = this.animationRange || this.model.range.slice(0) || [NaN,NaN];
        this.animationRange = range;
        //set current value to correct location if the timer isn't running yet.
        if(!this.timer && setTime !== false || setTime === true) {
            this.currentValue = range[(this.step > 0) ? 0 : 1];
        }
        if(range[0] != oldRange[0] || range[1] != oldRange[1]) {
            this.events.triggerEvent("rangemodified");
        }
    },

    /**
     * APIMethod: setAnimationStart
     * Sets the start value for an animation. If the step is negative then this
     * sets the maximum value in the control's range parameter. Will only effect
     * the currentValue if an animation has not begun.
     *
     * Parameters:
     * value - {Number}
     */
    setAnimationStart : function(value) {
        if(this.step>0){
            this.setAnimationRange([value,this.animationRange[1]]);
        } else {
            this.setAnimationRange([this.animationRange[0],value]);
        }
    },

    /**
     * APIMethod: setAnimationEnd
     * Sets the end value for an animation. If the step is negative then this
     * sets the minimum value in the control's range parameter. Will not effect
     * the current value.
     *
     * Parameters:
     * value - {Number}
     */
    setAnimationEnd : function(value) {
        //set the end but don't change current time
        if(this.step>0){
            this.setAnimationRange([this.animationRange[0],value], false);
        } else {
            this.setAnimationRange([value,this.animationRange[1]], false);
        }
    },

    /**
     * APIMethod:setCurrentValue
     * Manually sets the currentValue used in the control's animation.
     *
     * Parameters:
     * value - {Number}
     * silent - {Boolean} true to prevent tick event from firing
     *   default is false.
     */
    setCurrentValue : function(value, silent) {
        if(this.snapToList && this.modelCache.values) {
            var values = this.modelCache.values;
            var nearest = OpenLayers.Control.DimensionManager.findNearestValues(value, values);
            if(!nearest){
                return;
            }
            var index = this.lastValueIndex;
            if(nearest.exact > -1){
                index = nearest.exact;
            } else if(nearest.before > -1 &&  nearest.after > -1) {
                //requested value is somewhere between 2 valid values
                //find the actual closest one.
                var bdiff = Math.abs(values[nearest.before] - this.currentValue);
                var adiff = Math.abs(this.currentValue - values[nearest.after]);
                index = (adiff > bdiff) ? nearest.before : nearest.after;
            } else if (nearest.before > -1){
                index = nearest.before;
            } else if (nearest.after >-1){
                index = nearest.after;
            }
            this.currentValue = values[index];
            if (index === this.lastValueIndex) {
                silent = true;
            }
            this.lastValueIndex = index;
        }
        else {
            this.currentValue = value;
        }
        if(silent !== true){
            this.events.triggerEvent('tick', {
                'currentValue' : this.currentValue
            });
        }
    },

    /**
     * APIMethod:setFrameRate
     * Sets the control's playback frameRate (ticks/second)
     * Parameters: {Number} rate - the ticks/second rate
     */
    setFrameRate: function(rate){
        var playing = !!this.timer;
        this.clearTimer();
        this.frameRate = rate;
        if(playing){
            //this.tick();
            this.timer = setInterval(OpenLayers.Function.bind(this.tick, this), 1000 / this.frameRate);
        }
    },
    /**
     * APIMethod:reset
     * Resets the current value to the animation start value. Fires the 'reset'
     *    event.
     *
     * Returns:
     * {Number} the control's currentValue, which is also the control's start
     *    value
     */
    reset : function(looped) {
        this.clearTimer();
        this.setCurrentValue(this.animationRange[(this.step > 0) ? 0 : 1]);
        this.events.triggerEvent('reset', {
            'looped' : !!looped
        });
        return this.currentValue;
    },

    /**
     * APIMethod: incrementValue
     * Moves the current animation value forward by the specified step
     *
     * Parameters:
     * step - {Number}
     */
    incrementValue : function(step) {
        var newVal;
        if(this.dimension == 'time' && this.timeUnits){
            newVal = this.incrementTimeValue();
        } else {
            step = step || this.step;
            newVal = parseFloat(this.currentValue) + parseFloat(step);
        }
        this.setCurrentValue(newVal, true);
    },

    /**
     * Method: incrementTimeValue
     * (Private) Returns a new value incremented by step * timeUnit
     *
     * Parameter:
     * step - {Number} number of time units to advance by
     * timeUnits - {OpenLayers.TimeUnit}
     * value - {Date}/{Number}
     *
     * Returns:
     * {Number} the new value
     */
    incrementTimeValue : function(step, timeUnits, value){
        step = step || this.timeStep;
        timeUnits = timeUnits || this.timeUnits;
        value = value || this.currentValue;
        if(!(value instanceof Date)){
            value = new Date(value);
        }
        var newPart = parseFloat(value['getUTC'+timeUnits]()) + parseFloat(step);
        value['setUTC'+timeUnits](newPart);
        return value.getTime();
    },

    /**
     * Method: buildAgents
     * Creates the agents "managed" by this control.
     *
     * Parameters:
     * model - {OpenLayers.Dimension.Model} or {OpenLayers.Layer} with dimensional metadata
     *    Defaults to this.model. Also supports passing a single layer with
     *     dimensional metadata (ie layer.metadata.timeInfo).
     * dimension - {String} (OPTIONAL) Dimension agents will control.
     *    Defaults to this.dimension
     *
     * Returns:
     * {Array(<OpenLayers.Dimension.Agent>)}
     */
    buildAgents : function(model, dimension) {
        model = model || this.model;
        if(!model){ return []; }
        dimension = dimension || this.dimension || this.model.dimension;
        var layers = model.layers;
        if(!layers && model instanceof OpenLayers.Layer && model.metadata[dimension+'Info']){
            layers = [model];
            model = model.metadata[dimension+'Info'];
        }
        var layerTypes = {};
        var agents = [], agent;
        //categorize layers and separate into arrays for use in subclasses
        for(var i = 0, len = layers.length; i < len; i++) {
            var lyr = layers[i];
            if(!((lyr.dimensions && dimension in lyr.dimensions) || (lyr.metadata && dimension+'Info' in lyr.metadata))){
                //don't build agents for layers without this dimension
                continue;
            }
            //allow user specified overrides and custom behavior
            if(lyr.dimensionAgent) {
                if(lyr.dimensionAgent instanceof Function) {
                    agent = new OpenLayers.Dimension.Agent({
                        onTick : lyr.dimensionAgent,
                        layers : [lyr],
                        'dimension' : dimension,
                        dimensionManager : this
                    });
                    delete lyr.dimensionAgent;
                }
                this.events.on({
                    tick : agent.onTick,
                    scope : agent
                });
                agents.push(agent);
            }
            else {
                var lyrClass = lyr.CLASS_NAME.match(/\.Layer\.(\w+)/)[1];
                if(!OpenLayers.Dimension.Agent[lyrClass]) {
                    lyrClass = 'base';
                    console.warn("No OpenLayers.Dimension.Agent subclass available for " + lyr.CLASS_NAME + ". Using base class instead");
                }
                if(!layerTypes[lyrClass]) {
                    layerTypes[lyrClass] = [];
                }
                layerTypes[lyrClass].push(lyr);
            }
        }

        //create subclassed dimension agents
        for(var k in layerTypes) {
            var agentOpts = {
                layers : layerTypes[k],
                'dimension' : dimension,
                dimensionManager : this
            };

            if(this.agentOptions && this.agentOptions[k]) {
                OpenLayers.Util.applyDefaults(agentOpts, this.agentOptions[k]);
            }

            if(k == 'base'){
                agent = new OpenLayers.Dimension.Agent(agentOpts);
            } else {
                agent = new OpenLayers.Dimension.Agent[k](agentOpts);
            }

            this.events.on({
                'tick' : agent.onTick,
                scope : agent
            });
            agents.push(agent);
        }
        return (agents.length) ? agents : null;
    },

    removeAgentLayer : function(lyr) {
        //find the agent with the layer
        if(this.agents && this.agents.length){
            for(var i = 0, len = this.agents.length; i < len; i++) {
                var agent = this.agents[i];
                if(OpenLayers.Util.indexOf(agent.layers, lyr) > -1) {
                    agent.removeLayer(lyr);
                    //if the agent doesn't handle any layers, get rid of it
                    if(!agent.layers || !agent.layers.length) {
                        this.agents.splice(i, 1);
                        agent.destroy();
                    }
                    break;
                }
            }
        }
    },

    addAgentLayer : function(layer) {
        var added = false;
        var agentClass = layer.CLASS_NAME.match(/\.Layer\.(\w+)/)[1];
        if(agentClass in OpenLayers.Dimension.Agent) {
            if(!this.agents){ this.agents = []; }
            for(var i = 0, len = this.agents.length; i < len; i++) {
                if(!layer.dimensionAgent && this.agents[i] instanceof OpenLayers.Dimension.Agent[agentClass]) {
                    this.agents[i].addLayer(layer);
                    added = true;
                    break;
                }
            }
        }
        if(!added) {
            var agents = this.buildAgents(layer);
            if(agents) {
                this.agents.push(agents[0]);
                added = true;
            }
        }
        return added;
    },

    syncToModel: function(model){
        model = model || this.model;
        this.modelCache = {
            range: model.range,
            values: model.values,
            resolution: model.resolution
        };
        return this.modelCache;
    },

    onModelRangeModified: function(evtObj){
        var range = evtObj.range;
        this.syncToModel(evtObj.object);
        this.setAnimationRange(range);
    },

    onModelValuesModified: function(evtObj){
        var values = evtObj.values;
        this.syncToModel(evtObj.object);
    },

    onModelLayerAdded: function(evtObj){
        this.addAgentLayer(evtObj.layer);
    },

    onModelLayerRemoved: function(evtObj){
        this.removeAgentLayer(evtObj.layer);
    },

    guessPlaybackRate : function(model) {
        if(!this.agents) {
            return;
        } else {
            model = model || this.model;
            if(model.values) {
                this.snapToList = true;
            } else {
                var settings = model.guessPlaybackRate();
                OpenLayers.Util.extend(this, settings);
            }
        }
    },

    canTickCheck : function() {
        var canTick = false;
        for(var i = 0, len = this.agents.length; i < len; i++) {
            canTick = this.agents[i].canTick;
            if(!canTick) {
                break;
            }
        }
        return canTick;
    },

    clearTimer : function() {
        if(this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    },

    CLASS_NAME : 'OpenLayers.Control.DimensionManager'
});

/** Static Methods **/

OpenLayers.Util.extend(OpenLayers.Control.DimensionManager, {

    /**
     * Method: findNearestValues
     *    Finds the nearest value(s) index for a given test value. If an exact
     *    match is found, it will return the index for that value. However, if
     *    no exact match is found, then it will return the indexes before &
     *    after the test values. If the nearest value is a the end of the range
     *    then it returns -1 for the other values.
     * Parameters:
     *    testValue - {Number} the value to test against the value array.
     *    values - {Array{Number}} the sorted value array.
     * Returns: {Object} or {Boolean} with the following properties:
     *    exact, before, after
     *    All values will be either -1 or the index of the appropriate key. If
     *    an exact value is found both 'before'  and 'after' will always be -1.
     *    If the test value is outside of the range of the values array, then
     *    the function returns false.
     */

    findNearestValues : function(testValue, values) {
        var retObj = {
            exact : -1,
            before : -1,
            after : -1
        };
        //first check if this value is in the array
        var index = OpenLayers.Util.indexOf(values, testValue);
        if(index > -1) {
            //found an exact value
            retObj.exact = index;
        }
        else {
            //no exact value was found. test that this is even in the range
            if(testValue < values[0] || testValue > values[values.length - 1]) {
                //outside of the range, return false
                return false;
            }
            else {
                //value is within the range, find the nearest indices
                for(var i = 0, len = values.length; i < len; i++) {
                    var diff = testValue - values[i];
                    if(diff < 0) {
                        retObj.after = i;
                        retObj.before = i - 1;
                        break;
                    }
                    else {
                        retObj.before = i;
                    }
                }
            }
        }
        return retObj;
    }

});
