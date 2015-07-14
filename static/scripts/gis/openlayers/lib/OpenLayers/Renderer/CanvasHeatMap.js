/* Copyright (c) 2006-2008 MetaCarta, Inc., published under the Clear BSD
 * license.  See http://svn.openlayers.org/trunk/openlayers/license.txt for the
 * full text of the license. */

/**
 * @requires OpenLayers/Renderer/Canvas.js
 */

/**
 * Class: OpenLayers.Renderer.Canvas 
 * A renderer based on the 2D 'canvas' drawing element.element
 * 
 * Inherits:
 *  - <OpenLayers.Renderer>
 */
OpenLayers.Renderer.CanvasHeatMap = OpenLayers.Class(OpenLayers.Renderer.Canvas, {
    
    /**
     * APIProperty: pointSize
     * {Integer} The radius used to draw the points.
     */
    pointSize: null,

    /**
     * APIProperty: colorSchema
     * {Array} The coloring schema for the heat map, for example:
     * 
     *      var schema = [
     *          [0, 'rgba(255, 255, 255, 0)'],  
     *          [0.05, '#35343d'],  
     *          [0.15, '#050555'],  
     *          [0.3, '#00eaf2'],  
     *          [0.45, '#00b441'],  
     *          [0.6, '#dcfc05'],  
     *          [0.8, '#ff0101'],  
     *          [1, '#ffeded']
     *      ];
     */    
    colorSchema: null,
    
    /**
     * APIProperty: renderAsync
     * {Boolean} Run the heat map generation in a web worker?
     */
    renderAsync: false,

    /**
     * APIProperty: heatMapWebWorkerPath
     * {String} Path to the heat map webworker script (heatmap-webworker.js). This
     *      property must be set, if 'renderAsync' is set to true.
     */    
    heatMapWebWorkerPath: "heatmap-webworker.js",

    /**
     * Property: lastRenderTask
     * {Object} Reference to the last requested render task. When a new heat map
     *      is requested while the old heat map is not finished rendering in a 
     *      web worker, this property is used to prevent that the old heat map
     *      is displayed.
     */  
    lastRenderTask: null,

    /**
     * Property: EVENT_TYPES
     * {Array} Event 'renderProgress' is triggered during the heat map generation
     *      in a web worker.
     */     
    EVENT_TYPES: ["renderProgress"],

    /**
     * APIProperty: events
     * {<OpenLayers.Events>}
     */    
    events: null,
    
    /**
     * Constructor: OpenLayers.Renderer.CanvasHeatMap
     *
     * Parameters:
     * containerID - {<String>} 
     * options - {Object} Hashtable of extra options to tag onto the renderer. Valid keys
     *      are 'pointSize' and 'colorSchema'.
     */
    initialize: function(containerID, options) {
        OpenLayers.Renderer.Canvas.prototype.initialize.apply(this, arguments);
        this.events = new OpenLayers.Events(this, null, this.EVENT_TYPES);
        
        // get renderer options
        OpenLayers.Util.extend(this, options);
    },

    /**
     * Method: redraw
     * Called on every pan and zoom: redraws the heat map.
     */
    redraw: function() {
        if (this.locked) {
            return;
        }
        
        // create the heat map and set the properties
        var heatMap = this.setupHeatMap();
        
        // add every feature to the heat map
        this.addFeatures(heatMap);
        
        // and then render the heat map to the canvas 
        this.renderHeatMap(heatMap);

    },
    
    /**
     * Method: setupHeatMap
     * Creates a heat map and sets the properties.
     * 
     * Returns:
     * {HeatMap}
     */
    setupHeatMap: function() {
        var heatMap = new HeatMap(this.root.width, this.root.height);
        
        if (this.pointSize !== null) {
            heatMap.pointSize = this.pointSize;
        }
        if (this.colorSchema !== null) {
            heatMap.colorSchema = this.colorSchema;
        }
        
        return heatMap;        
    },

    /**
     * Method: addFeatures
     * Adds the features of the layer to the heat map.
     * 
     * Parameters:
     * heatMap - {HeatMap}
     */    
    addFeatures: function(heatMap) {
        for (var i = 0; i < this.featuresOrdered.length; i++) {
            var feature = this.featuresOrdered[i];
            
            if (!feature.geometry) { 
                continue; 
            }
            
            var pt = this.getLocalXY(feature.geometry);
            heatMap.addPoint(pt[0], pt[1]);
        }        
    },

    /**
     * Method: renderHeatMap
     * Renders the heat map. If 'renderAsync' is set to false,
     * the heat map is directly rendererd on the layer's canvas.
     * Otherwise the rendering is executed in a web worker.
     * 
     * Parameters:
     * heatMap - {HeatMap}
     */
    renderHeatMap: function(heatMap) {
        if (!this.renderAsync) {
            heatMap.create(this.root);    
        } else {
            // use web workers to run the heat map generation in background 
            this.renderHeatMapAsync(heatMap);
        }        
    },

    /**
     * Method: renderHeatMapAsync
     * Start the heat map generation in a web worker.
     * 
     * Parameters:
     * heatMap - {HeatMap}
     */    
    renderHeatMapAsync: function(heatMap) {
        this.root.width = this.root.width;
           
        var renderTask = {
            renderer: this    
        };
        this.lastRenderTask = renderTask;
        
        // set the callback function, when the heat map generation has finished
        var handlerDone = function(resultCanvas) {
            if (renderTask.renderer.lastRenderTask !== renderTask) {
                return;    
            }
            
            var canvas = renderTask.renderer.root;
            canvas.getContext("2d").drawImage(resultCanvas, 0, 0);
        };
        
        // display the progress in a progress bar
        var handlerProgress = function(progress) {
            if (renderTask.renderer.lastRenderTask !== renderTask) {
                return;    
            }
            
            var event = {
                progress: progress
            };
            renderTask.renderer.events.triggerEvent("renderProgress", event);
        };
        
        var handlerError = function(error) {
            console.log(error);
        };
        
        heatMap.createAsync(
                    null, 
                    handlerDone, 
                    handlerProgress, 
                    handlerError,
                    this.heatMapWebWorkerPath
        );          
    },

    CLASS_NAME: "OpenLayers.Renderer.CanvasHeatMap"
});
