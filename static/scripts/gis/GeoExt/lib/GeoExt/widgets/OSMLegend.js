/**
 * Copyright (c) 2008-2013 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/**
 * @include GeoExt/widgets/LegendImage.js
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
 *      Show a legend image in a BoxComponent and make sure load errors are 
 *      dealt with.
 */
GeoExt.OSMLegend = Ext.extend(GeoExt.LayerLegend, {

    /** private: method[initComponent]
     *  Initializes the legend image component. 
     */
    initComponent: function() {
        GeoExt.OSMLegend.superclass.initComponent.call(this);
        this.add(new GeoExt.LegendImage({
            url: this.layerRecord.get("legendURL")
        }));
    },
    
    /** private: method[update]
     *  Private override
     */
    update: function() {
        GeoExt.OSMLegend.superclass.update.apply(this, arguments);
        this.items.get(1).setUrl(this.layerRecord.get("legendURL"));
    }

});

/** private: method[supports]
 *  Private override
 */
GeoExt.OSMLegend.supports = function(layerRecord) {
    return layerRecord.get("legendURL") == null ? 0 : 10;
};

/** api: legendtype = gx_urllegend */
GeoExt.LayerLegend.types["gx_urllegend"] = GeoExt.OSMLegend;

/** api: xtype = gx_urllegend */
Ext.reg('gx_urllegend', GeoExt.OSMLegend);
