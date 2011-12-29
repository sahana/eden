/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the BSD license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @include widgets/FillSymbolizer.js
 * @include widgets/form/FontComboBox.js
 */

/** api: (define)
 *  module = gxp
 *  class = TextSymbolizer
 *  base_link = `Ext.Panel <http://extjs.com/deploy/dev/docs/?class=Ext.Panel>`_
 */
Ext.namespace("gxp");

/** api: constructor
 *  .. class:: TextSymbolizer(config)
 *   
 *      Form for configuring a text symbolizer.
 */
gxp.TextSymbolizer = Ext.extend(Ext.Panel, {
    
    /** api: config[fonts]
     *  ``Array(String)``
     *  List of fonts for the font combo.  If not set, defaults to the list
     *  provided by the :class:`gxp.FontComboBox`.
     */
    fonts: undefined,
    
    /** api: config[symbolizer]
     *  ``Object``
     *  A symbolizer object that will be used to fill in form values.
     *  This object will be modified when values change.  Clone first if
     *  you do not want your symbolizer modified.
     */
    symbolizer: null,
    
    /** api: config[defaultSymbolizer]
     *  ``Object``
     *  Default symbolizer properties to be used where none provided.
     */
    defaultSymbolizer: null,
    
    /** api: config[attributes]
     *  :class:`GeoExt.data.AttributeStore`
     *  A configured attributes store for use in the filter property combo.
     */
    attributes: null,
    
    /** api: config[colorManager]
     *  ``Function``
     *  Optional color manager constructor to be used as a plugin for the color
     *  field.
     */
    colorManager: null,

    /** private: property[haloCache]
     *  ``Object``
     *  Stores halo properties while fieldset is collapsed.
     */
    haloCache: null,
    
    border: false,    
    layout: "form",
    
    /** i18n */
    labelValuesText: "Label values",
    haloText: "Halo",
    sizeText: "Size",
    
    initComponent: function() {
        
        if(!this.symbolizer) {
            this.symbolizer = {};
        }        
        Ext.applyIf(this.symbolizer, this.defaultSymbolizer);

        this.haloCache = {};

        var defAttributesComboConfig = {
            xtype: "combo",
            fieldLabel: this.labelValuesText,
            store: this.attributes,
            editable: false,
            triggerAction: "all",
            allowBlank: false,
            displayField: "name",
            valueField: "name",
            value: this.symbolizer.label && this.symbolizer.label.replace(/^\${(.*)}$/, "$1"),
            listeners: {
                select: function(combo, record) {
                    this.symbolizer.label = "${" + record.get("name") + "}";
                    this.fireEvent("change", this.symbolizer);
                },
                scope: this
            },
            width: 120
        };
        this.attributesComboConfig = this.attributesComboConfig || {};
        Ext.applyIf(this.attributesComboConfig, defAttributesComboConfig);
        
        this.labelWidth = 80;
        
        this.items = [this.attributesComboConfig, {
            cls: "x-html-editor-tb",
            style: "background: transparent; border: none; padding: 0 0em 0.5em;",
            xtype: "toolbar",
            items: [{
                xtype: "gxp_fontcombo",
                fonts: this.fonts || undefined,
                width: 110,
                value: this.symbolizer.fontFamily,
                listeners: {
                    select: function(combo, record) {
                        this.symbolizer.fontFamily = record.get("field1");
                        this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                }
            }, {
                xtype: "tbtext",
                text: this.sizeText + ": "
            }, {
                xtype: "numberfield",
                allowNegative: false,
                emptyText: OpenLayers.Renderer.defaultSymbolizer.fontSize,
                value: this.symbolizer.fontSize,
                width: 30,
                listeners: {
                    change: function(field, value) {
                        value = parseFloat(value);
                        if (isNaN(value)) {
                            delete this.symbolizer.fontSize;
                        } else {
                            this.symbolizer.fontSize = value;
                        }
                        this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                }
            }, {
                enableToggle: true,
                cls: "x-btn-icon",
                iconCls: "x-edit-bold",
                pressed: this.symbolizer.fontWeight === "bold",
                listeners: {
                    toggle: function(button, pressed) {
                        this.symbolizer.fontWeight = pressed ? "bold" : "normal";
                        this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                }
            }, {
                enableToggle: true,
                cls: "x-btn-icon",
                iconCls: "x-edit-italic",
                pressed: this.symbolizer.fontStyle === "italic",
                listeners: {
                    toggle: function(button, pressed) {
                        this.symbolizer.fontStyle = pressed ? "italic" : "normal";
                        this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                }
            }]
        }, {
            xtype: "gxp_fillsymbolizer",
            symbolizer: this.symbolizer,
            defaultColor: OpenLayers.Renderer.defaultSymbolizer.fontColor,
            checkboxToggle: false,
            autoHeight: true,
            width: 213,
            labelWidth: 70,
            plugins: this.colorManager && [new this.colorManager()],
            listeners: {
                change: function(symbolizer) {
                    this.fireEvent("change", this.symbolizer);
                },
                scope: this
            }
        }, {
            xtype: "fieldset",
            title: this.haloText,
            checkboxToggle: true,
            collapsed: !(this.symbolizer.haloRadius || this.symbolizer.haloColor || this.symbolizer.haloOpacity),
            autoHeight: true,
            labelWidth: 50,
            items: [{
                xtype: "numberfield",
                fieldLabel: this.sizeText,
                anchor: "89%",
                allowNegative: false,
                emptyText: OpenLayers.Renderer.defaultSymbolizer.haloRadius,
                value: this.symbolizer.haloRadius,
                listeners: {
                    change: function(field, value) {
                        value = parseFloat(value);
                        if (isNaN(value)) {
                            delete this.symbolizer.haloRadius;
                        } else {
                            this.symbolizer.haloRadius = value;
                        }
                        this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                }
            }, {
                xtype: "gxp_fillsymbolizer",
                symbolizer: {
                    fillColor: ("haloColor" in this.symbolizer) ? this.symbolizer.haloColor : OpenLayers.Renderer.defaultSymbolizer.haloColor,
                    fillOpacity: ("haloOpacity" in this.symbolizer) ? this.symbolizer.haloOpacity : OpenLayers.Renderer.defaultSymbolizer.haloOpacity
                },
                defaultColor: OpenLayers.Renderer.defaultSymbolizer.haloColor,
                checkboxToggle: false,
                width: 190,
                labelWidth: 60,
                plugins: this.colorManager && [new this.colorManager()],
                listeners: {
                    change: function(symbolizer) {
                        this.symbolizer.haloColor = symbolizer.fillColor;
                        this.symbolizer.haloOpacity = symbolizer.fillOpacity;
                        this.fireEvent("change", this.symbolizer);
                    },
                    scope: this
                }
            }],
            listeners: {
                collapse: function() {
                    this.haloCache = {
                        haloRadius: this.symbolizer.haloRadius,
                        haloColor: this.symbolizer.haloColor,
                        haloOpacity: this.symbolizer.haloOpacity
                    };
                    delete this.symbolizer.haloRadius;
                    delete this.symbolizer.haloColor;
                    delete this.symbolizer.haloOpacity;
                    this.fireEvent("change", this.symbolizer)
                },
                expand: function() {
                    Ext.apply(this.symbolizer, this.haloCache);
                    /**
                     * Start workaround for
                     * http://projects.opengeo.org/suite/ticket/676
                     */
                    this.doLayout();
                    /**
                     * End workaround for
                     * http://projects.opengeo.org/suite/ticket/676
                     */                    
                    this.fireEvent("change", this.symbolizer);
                },
                scope: this
            }
        }];

        this.addEvents(
            /**
             * Event: change
             * Fires before any field blurs if the field value has changed.
             *
             * Listener arguments:
             * symbolizer - {Object} A symbolizer with text related properties
             *     updated.
             */
            "change"
        ); 
 
        gxp.TextSymbolizer.superclass.initComponent.call(this);
        
    }
    
    
});

/** api: xtype = gxp_textsymbolizer */
Ext.reg('gxp_textsymbolizer', gxp.TextSymbolizer); 
