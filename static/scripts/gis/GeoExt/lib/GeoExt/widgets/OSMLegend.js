/**
 * Copyright (c) 2008-2013 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/**
 * @requires GeoExt/widgets/LayerLegend.js
 */

/** api: (define)
 *  module = GeoExt
 *  class = OSMLegend
 */

/** api: (extends)
 * GeoExt/widgets/LayerLegend.js
 */

Ext.namespace('GeoExt');

/** api: constructor
 *  .. class:: OSMLegend(config)
 *
 *      Show a legend html in a BoxComponent and make sure load errors are 
 *      dealt with.
 */
GeoExt.OSMLegend = Ext.extend(GeoExt.LayerLegend, {

    /** api: config[url]
     *  ``String``  The url of the html to load
     */
    url: 'http://www.openstreetmap.org/key',

    /** private: method[initComponent]
     *  Initializes the legend html component. 
     */
    initComponent: function() {
        GeoExt.OSMLegend.superclass.initComponent.call(this);
        this.add(new Ext.BoxComponent({
            autoEl: {
                tag: 'div'
            }
        }));
        Ext.Ajax.request({
            method: 'GET',
            url: this.url,
            success: function (response) {
                // @ToDo: Why is response empty via AJAX when URL works fine direct in browser?
                this.getEl().dom.outerHTML = response.responseText;
            }
        });
    },
    
    /** private: method[update]
     *  Private override
     */
    update: function() {
        GeoExt.OSMLegend.superclass.update.apply(this, arguments);
        //this.items.get(1).setUrl(this.url);
    }

});

/** private: method[supports]
 *  Private override
 */
GeoExt.OSMLegend.supports = function(layerRecord) {
    // @ToDo: Filter by URL?
    return layerRecord.getLayer() instanceof OpenLayers.Layer.TMS ? 1 : 0;
};

/** api: legendtype = gx_osmlegend */
GeoExt.LayerLegend.types["gx_osmlegend"] = GeoExt.OSMLegend;

/** api: xtype = gx_osmlegend */
Ext.reg('gx_osmlegend', GeoExt.OSMLegend);
