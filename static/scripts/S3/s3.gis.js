/**
 * Used by the Map (modules/s3gis.py)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

/* Global vars */
var map;
// @ToDo: move this to S3.gis when restoring this
//var printProvider;
S3.gis.layers_all = new Array();
S3.gis.format_geojson = new OpenLayers.Format.GeoJSON();
S3.gis.dirs = new Array();
// Images
S3.gis.ajax_loader = S3.Ap.concat('/static/img/ajax-loader.gif');
S3.gis.marker_url = S3.Ap.concat('/static/img/markers/');
OpenLayers.ImgPath = S3.Ap.concat('/static/img/gis/openlayers/');
// avoid pink tiles
OpenLayers.IMAGE_RELOAD_ATTEMPTS = 3;
OpenLayers.Util.onImageLoadErrorColor = 'transparent';
OpenLayers.ProxyHost = S3.Ap.concat('/gis/proxy?url=');
// See http://crschmidt.net/~crschmidt/spherical_mercator.html#reprojecting-points
S3.gis.proj4326 = new OpenLayers.Projection('EPSG:4326');
S3.gis.proj4236 = new OpenLayers.Projection('EPSG:4236');
S3.gis.projection_current = new OpenLayers.Projection('EPSG:' + S3.gis.projection);
S3.gis.options = {
    displayProjection: S3.gis.proj4326,
    projection: S3.gis.projection_current,
    // Use Manual stylesheet download (means can be done in HEAD to not delay pageload)
    theme: null,
    // This means that Images get hidden by scrollbars
    //paddingForPopups: new OpenLayers.Bounds(50, 10, 200, 300),
    units: S3.gis.units,
    maxResolution: S3.gis.maxResolution,
    maxExtent: new OpenLayers.Bounds(S3.gis.maxExtent[0], S3.gis.maxExtent[1], S3.gis.maxExtent[2], S3.gis.maxExtent[3]),
    numZoomLevels: S3.gis.numZoomLevels
};
// Default values if not set by the layer
// Also in modules/s3/s3gis.py
// http://dev.openlayers.org/docs/files/OpenLayers/Strategy/Cluster-js.html
S3.gis.cluster_distance = 20;    // pixels
S3.gis.cluster_threshold = 2;   // minimum # of features to form a cluster
// Counter to know whether there are layers still loading
S3.gis.layers_loading = 0;

// Register Plugins
S3.gis.plugins = [];
function registerPlugin(plugin) {
    S3.gis.plugins.push(plugin);
}

/* Main Start Function
   - called by yepnope callback */
//Ext.onReady(function() {
//    S3.gis.show_map();
//}
S3.gis.show_map = function() {
    // Configure the Viewport
    if (S3.gis.lat && S3.gis.lon) {
        S3.gis.center = new OpenLayers.LonLat(S3.gis.lon, S3.gis.lat);
        S3.gis.center.transform(S3.gis.proj4326, S3.gis.projection_current);
    } else if (S3.gis.bottom_left && S3.gis.top_right) {
        s3_gis_setCenter(S3.gis.bottom_left, S3.gis.top_right);
    }

    //Ext.onReady(function() {
        // Build the OpenLayers map
        addMap();

        // Add the GeoExt UI
        addMapUI();

        // If we were instantiated with bounds, use these now
        if ( S3.gis.bounds ) {
            map.zoomToExtent(S3.gis.bounds);
        }

        // Toolbar Tooltips
        Ext.QuickTips.init();
    //}
}

// Configure the Viewport
function s3_gis_setCenter(bottom_left, top_right) {
    bottom_left = new OpenLayers.LonLat(bottom_left[0], bottom_left[1]);
    bottom_left.transform(S3.gis.proj4326, S3.gis.projection_current);
    var left = bottom_left.lon;
    var bottom = bottom_left.lat;
    top_right = new OpenLayers.LonLat(top_right[0], top_right[1]);
    top_right.transform(S3.gis.proj4326, S3.gis.projection_current);
    var right = top_right.lon;
    var top = top_right.lat;
    S3.gis.bounds = OpenLayers.Bounds.fromArray([left, bottom, right, top]);
    S3.gis.center = S3.gis.bounds.getCenterLonLat();
}

// Build the OpenLayers map
function addMap() {
    map = new OpenLayers.Map('center', S3.gis.options);

    // Layers
    // defined in s3.gis.layers.js
    addLayers();

    // Controls (add these after the layers)
    // defined in s3.gis.controls.js
    addControls();
}

// Add the GeoExt UI
function addMapUI() {
    S3.gis.mapPanel = new GeoExt.MapPanel({
        height: S3.gis.map_height,
        width: S3.gis.map_width,
        id: 'mappanel',
        xtype: 'gx_mappanel',
        map: map,
        center: S3.gis.center,
        zoom: S3.gis.zoom,
        plugins: []
    });

    // Set up shortcuts to allow GXP Plugins to work
    S3.gis.portal = Object();
    S3.gis.portal.map = S3.gis.mapPanel;

    if (S3.i18n.gis_legend || S3.gis.layers_wms) {
        for (var i = 0; i < map.layers.length; i++) {
            // Ensure that legendPanel knows about the Markers for our Feature layers
            if (map.layers[i].legendURL) {
                S3.gis.mapPanel.layers.data.items[i].data.legendURL = map.layers[i].legendURL;
            }
            // Ensure that mapPanel knows about whether our WMS layers are queryable
            if (map.layers[i].queryable) {
                S3.gis.mapPanel.layers.data.items[i].data.queryable = 1;
            }
        }
    }

    // Which Elements do we want in our mapWindow?
    // @ToDo: Move all these to Plugins

    // Layer Tree
    addLayerTree();
    var items = [S3.gis.layerTree];

    // WMS Browser
    if (S3.gis.wms_browser_url) {
        addWMSBrowser();
        if (S3.gis.wmsBrowser) {
            items.push(S3.gis.wmsBrowser);
        }
    }

    // Print Panel (currently still defined in modules/s3/s3gis.py)
    if (S3.gis.printFormPanel) {
        items.push(S3.gis.printFormPanel);
    }

    // Legend Panel
    if (S3.i18n.gis_legend) {
       S3.gis.legendPanel = new GeoExt.LegendPanel({
            id: 'legendpanel',
            title: S3.i18n.gis_legend,
            defaults: {
                labelCls: 'mylabel',
                style: 'padding:4px'
            },
            bodyStyle: 'padding:4px',
            autoScroll: true,
            collapsible: true,
            collapseMode: 'mini',
            lines: false
        });
        items.push(S3.gis.legendPanel);
    }

    // Plugins
    for ( var i = 0; i < S3.gis.plugins.length; ++i ) {
        S3.gis.plugins[i].setup(map);
        S3.gis.plugins[i].addToMapWindow(items);
    }

    // West Panel
    S3.gis.mapWestPanel = new Ext.Panel({
        id: 'tools',
        header: false,
        border: false,
        split: true,
        items: items
    });

    // Instantiate the main Map window
    if (S3.gis.window) {
        addMapWindow();
    } else {
        // Embedded Map
        addMapPanel();
    }
}

// Put into a Container to allow going fullscreen from a BorderLayout
function addWestPanel() {
    if ( undefined == S3.gis.west_collapsed ) {
        S3.gis.west_collapsed = false;
    }
    S3.gis.mapWestPanelContainer = new Ext.Panel({
        region: 'west',
        header: false,
        border: true,
        width: 250,
        autoScroll: true,
        collapsible: true,
        collapseMode: 'mini',
        collapsed: S3.gis.west_collapsed,
        items: [
            S3.gis.mapWestPanel
        ]
    });
};

// Put into a Container to allow going fullscreen from a BorderLayout
// We need to put the mapPanel inside a 'card' container for the Google Earth Panel
function addMapPanelContainer() {
    if (S3.gis.toolbar) {
        addToolbar();
    }
    S3.gis.mapPanelContainer = new Ext.Panel({
        layout: 'card',
        region: 'center',
        id: 'mappnlcntr',
        defaults: {
            // applied to each contained panel
            border: false
        },
        items: [
            S3.gis.mapPanel
        ],
        activeItem: 0,
        tbar: S3.gis.toolbar,
        scope: this
    });

    if (S3.gis.Google && S3.gis.Google.Earth) {
        // Instantiate afresh after going fullscreen as fails otherwise
        S3.gis.googleEarthPanel = new gxp.GoogleEarthPanel({
            mapPanel: S3.gis.mapPanel
        });
        // Add now rather than when button pressed as otherwise 1st press doesn't do anything
        S3.gis.mapPanelContainer.items.items.push(S3.gis.googleEarthPanel);
    }
};

// Create an embedded Map Panel
function addMapPanel() {
    addWestPanel();
    addMapPanelContainer();

    S3.gis.mapWin = new Ext.Panel({
        id: 'gis-map-panel',
        renderTo: 'map_panel',
        autoScroll: true,
        //maximizable: true,
        titleCollapse: true,
        height: S3.gis.map_height,
        width: S3.gis.map_width,
        layout: 'border',
        items: [
            S3.gis.mapWestPanelContainer,
            S3.gis.mapPanelContainer
        ]
    });
}

// Create a floating Map Window
// This is also called when an embedded map is made to go fullscreen
function addMapWindow() {
    addWestPanel();
    addMapPanelContainer();

    var mapWin = new Ext.Window({
        id: 'gis-map-window',
        collapsible: false,
        constrain: true,
        closable: !S3.gis.windowNotClosable,
        closeAction: 'hide',
        autoScroll: true,
        maximizable: S3.gis.maximizable,
        titleCollapse: false,
        height: S3.gis.map_height,
        width: S3.gis.map_width,
        layout: 'border',
        items: [
            S3.gis.mapWestPanelContainer,
            S3.gis.mapPanelContainer
        ]
    });

    mapWin.on("beforehide", function(mw){
    	if (mw.maximized) {
    		mw.restore();
    	}
    });

    // Set Options
    if (!S3.gis.windowHide) {
        // If the window is meant to be displayed immediately then display it now that it is ready
        mapWin.show();
        mapWin.maximize();
    }

    // pass to Global Scope
    S3.gis.mapWin = mapWin;
}

// Add LayerTree (to be called after the layers are added)
function addLayerTree() {

    // Default Folder for Base Layers
    var layerTreeBase = {
        text: S3.i18n.gis_base_layers,
        nodeType: 'gx_baselayercontainer',
        layerStore: S3.gis.mapPanel.layers,
        loader: {
            filter: function(record) {
                var layer = record.getLayer();
                return layer.displayInLayerSwitcher === true &&
                       layer.isBaseLayer === true &&
                       (layer.dir === undefined || layer.dir == '');
            }
        },
        leaf: false,
        expanded: true
    };

    // Default Folder for Overlays
    var layerTreeOverlays = {
        text: S3.i18n.gis_overlays,
        nodeType: 'gx_overlaylayercontainer',
        layerStore: S3.gis.mapPanel.layers,
        loader: {
            filter: function(record) {
                var layer = record.getLayer();
                return layer.displayInLayerSwitcher === true &&
                       layer.isBaseLayer === false &&
                       (layer.dir === undefined || layer.dir == '');
            }
        },
        leaf: false,
        expanded: true
    };

    var nodesArr = [ layerTreeBase, layerTreeOverlays ];

    // User-specified Folders
    var dirs = S3.gis.dirs;
    for (var i = 0; i < dirs.length; i++) {
        var folder = dirs[i];
        var child = {
            text: dirs[i],
            nodeType: 'gx_layercontainer',
            layerStore: S3.gis.mapPanel.layers,
            loader: {
                filter: (function(folder) {
                    return function(read) {
                        if (read.data.layer.dir !== 'undefined')
                            return read.data.layer.dir === folder;
                    }
                })(folder)
            },
            leaf: false,
           expanded: true
        }
        nodesArr.push(child);
    }

     var treeRoot = new Ext.tree.AsyncTreeNode({
        expanded: true,
        children: nodesArr
    });

    if (S3.i18n.gis_uploadlayer || S3.i18n.gis_properties) {
        var tbar = new Ext.Toolbar();
    } else {
        var tbar = null;
    }

    S3.gis.layerTree = new Ext.tree.TreePanel({
        id: 'treepanel',
        title: S3.i18n.gis_layers,
        loader: new Ext.tree.TreeLoader({applyLoader: false}),
        root: treeRoot,
        rootVisible: false,
        split: true,
        autoScroll: true,
        collapsible: true,
        collapseMode: 'mini',
        lines: false,
        tbar: tbar,
        enableDD: true
    });

    // Add/Remove Layers
    if (S3.i18n.gis_uploadlayer) {
        addRemoveLayersControl();
    }
    // Layer Properties
    if (S3.i18n.gis_properties) {
        addLayerPropertiesButton();
    }
}

// Add WMS Browser
function addWMSBrowser() {
    var root = new Ext.tree.AsyncTreeNode({
        expanded: true,
        loader: new GeoExt.tree.WMSCapabilitiesLoader({
            url: OpenLayers.ProxyHost + S3.gis.wms_browser_url,
            layerOptions: {buffer: 1, singleTile: false, ratio: 1, wrapDateLine: true},
            layerParams: {'TRANSPARENT': 'TRUE'},
            // customize the createNode method to add a checkbox to nodes
            createNode: function(attr) {
                attr.checked = attr.leaf ? false : undefined;
                return GeoExt.tree.WMSCapabilitiesLoader.prototype.createNode.apply(this, [attr]);
            }
        })
    });
    S3.gis.wmsBrowser = new Ext.tree.TreePanel({
        id: 'wmsbrowser',
        title: S3.gis.wms_browser_name,
        root: root,
        rootVisible: false,
        split: true,
        autoScroll: true,
        collapsible: true,
        collapseMode: 'mini',
        lines: false,
        listeners: {
            // Add layers to the map when checked, remove when unchecked.
            // Note that this does not take care of maintaining the layer
            // order on the map.
            'checkchange': function(node, checked) {
                if (checked === true) {
                    S3.gis.mapPanel.map.addLayer(node.attributes.layer);
                } else {
                    S3.gis.mapPanel.map.removeLayer(node.attributes.layer);
                }
            }
        }
    });
}

// Toolbar Buttons
// The buttons called from here are defined in s3.gis.controls.js
function addToolbar() {

    //var toolbar = S3.gis.mapPanelContainer.getTopToolbar();
    var toolbar = new Ext.Toolbar({
        id: 'gis_toolbar',
        // Height needed for the Throbber
        height: 34
    });

    var zoomfull = new GeoExt.Action({
        control: new OpenLayers.Control.ZoomToMaxExtent(),
        map: map,
        iconCls: 'zoomfull',
        // button options
        tooltip: S3.i18n.gis_zoomfull
    });

    var zoomout = new GeoExt.Action({
        control: new OpenLayers.Control.ZoomBox({ out: true }),
        map: map,
        iconCls: 'zoomout',
        // button options
        tooltip: S3.i18n.gis_zoomout,
        toggleGroup: 'controls'
    });

    var zoomin = new GeoExt.Action({
        control: new OpenLayers.Control.ZoomBox(),
        map: map,
        iconCls: 'zoomin',
        // button options
        tooltip: S3.i18n.gis_zoomin,
        toggleGroup: 'controls'
    });

    if (S3.gis.draw_feature == "active") {
        var pan_pressed = false;
        var point_pressed = true;
        var polygon_pressed = false;
    } else if (S3.gis.draw_polygon == "active") {
        var pan_pressed = false;
        var point_pressed = false;
        var polygon_pressed = true;
    } else {
        var pan_pressed = true;
        var point_pressed = false;
        var polygon_pressed = false;
    }

    S3.gis.panButton = new GeoExt.Action({
        control: new OpenLayers.Control.Navigation(),
        map: map,
        iconCls: 'pan-off',
        // button options
        tooltip: S3.i18n.gis_pan,
        toggleGroup: 'controls',
        allowDepress: true,
        pressed: pan_pressed
    });

    // Controls for Draft Features (unused)

    //var selectControl = new OpenLayers.Control.SelectFeature(S3.gis.draftLayer, {
    //    onSelect: onFeatureSelect,
    //    onUnselect: onFeatureUnselect,
    //    multiple: false,
    //    clickout: true,
    //    isDefault: true
    //});

    //var removeControl = new OpenLayers.Control.RemoveFeature(S3.gis.draftLayer, {
    //    onDone: function(feature) {
    //        console.log(feature)
    //    }
    //});

    //var selectButton = new GeoExt.Action({
        //control: selectControl,
    //    map: map,
    //    iconCls: 'searchclick',
        // button options
    //    tooltip: 'T("Query Feature")',
    //    toggleGroup: 'controls',
    //    enableToggle: true
    //});

    //var lineButton = new GeoExt.Action({
    //    control: new OpenLayers.Control.DrawFeature(S3.gis.draftLayer, OpenLayers.Handler.Path),
    //    map: map,
    //    iconCls: 'drawline-off',
    //    tooltip: 'T("Add Line")',
    //    toggleGroup: 'controls'
    //});

    //var dragButton = new GeoExt.Action({
    //    control: new OpenLayers.Control.DragFeature(S3.gis.draftLayer),
    //    map: map,
    //    iconCls: 'movefeature',
    //    tooltip: 'T("Move Feature: Drag feature to desired location")',
    //    toggleGroup: 'controls'
    //});

    //var resizeButton = new GeoExt.Action({
    //    control: new OpenLayers.Control.ModifyFeature(S3.gis.draftLayer, { mode: OpenLayers.Control.ModifyFeature.RESIZE }),
    //    map: map,
    //    iconCls: 'resizefeature',
    //    tooltip: 'T("Resize Feature: Select the feature you wish to resize & then Drag the associated dot to your desired size")',
    //    toggleGroup: 'controls'
    //});

    //var rotateButton = new GeoExt.Action({
    //    control: new OpenLayers.Control.ModifyFeature(S3.gis.draftLayer, { mode: OpenLayers.Control.ModifyFeature.ROTATE }),
    //    map: map,
    //    iconCls: 'rotatefeature',
    //    tooltip: 'T("Rotate Feature: Select the feature you wish to rotate & then Drag the associated dot to rotate to your desired location")',
    //    toggleGroup: 'controls'
    //});

    //var modifyButton = new GeoExt.Action({
    //    control: new OpenLayers.Control.ModifyFeature(S3.gis.draftLayer),
    //    map: map,
    //    iconCls: 'modifyfeature',
    //    tooltip: 'T("Modify Feature: Select the feature you wish to deform & then Drag one of the dots to deform the feature in your chosen manner")',
    //    toggleGroup: 'controls'
    //});

    //var removeButton = new GeoExt.Action({
    //    control: removeControl,
    //    map: map,
    //    iconCls: 'removefeature',
    //    tooltip: 'T("Remove Feature: Select the feature you wish to remove & press the delete key")',
    //    toggleGroup: 'controls'
    //});

    /* Add controls to Map & buttons to Toolbar */

    toolbar.add(zoomfull);

    if (navigator.geolocation) {
        // HTML5 geolocation is available :)
        addGeolocateControl(toolbar)
    }

    // Don't include the Nav controls in the Location Selector
    if (undefined === S3.gis.loc_select) {
        toolbar.add(zoomout);
        toolbar.add(zoomin);
        toolbar.add(S3.gis.panButton);
        toolbar.addSeparator();
    }

    // Navigation
    // @ToDo: Make these optional
    // Don't include the Nav controls in the Location Selector
    if (undefined === S3.gis.loc_select) {
        addNavigationControl(toolbar);
    }

    // Save Viewport
    if ((undefined === S3.gis.loc_select) && (S3.auth)) {
        addSaveButton(toolbar);
    }
    toolbar.addSeparator();

    // Measure Tools
    // @ToDo: Make these optional
    addMeasureControls(toolbar);

    // MGRS Grid PDFs
    if (S3.gis.mgrs_url) {
        addPdfControl(toolbar);
    }

    if (S3.gis.draw_feature || S3.gis.draw_polygon) {
        // Draw Controls
        toolbar.addSeparator();
        //toolbar.add(selectButton);
        if (S3.gis.draw_feature) {
            addPointControl(toolbar, point_pressed);
        }
        //toolbar.add(lineButton);
        if (S3.gis.draw_polygon) {
            addPolygonControl(toolbar, polygon_pressed, true);
        }
        //toolbar.add(dragButton);
        //toolbar.add(resizeButton);
        //toolbar.add(rotateButton);
        //toolbar.add(modifyButton);
        //toolbar.add(removeButton);
    }

    // WMS GetFeatureInfo
    // @ToDo: Add control if we add appropriate layers dynamically...
    if (S3.i18n.gis_get_feature_info) {
        addWMSGetFeatureInfoControl(toolbar);
    }

    // OpenStreetMap Editor
    if (S3.gis.osm_oauth) {
        addPotlatchButton(toolbar);
    }

    // Google Streetview
    if (S3.gis.Google && S3.gis.Google.StreetviewButton) {
        addGoogleStreetviewControl(toolbar);
    }

    // Google Earth
    try {
        // Only load Google layers if GoogleAPI downloaded ok
        // - allow rest of map to work offline
        if (S3.gis.Google.Earth) {
            google & addGoogleEarthControl(toolbar);
        }
    } catch(err) {};
    
    // Search box
    if (S3.i18n.gis_search) {
        var width = Math.min(350, (S3.gis.map_width - 680));
        var mapSearch = new GeoExt.ux.GeoNamesSearchCombo({
            map: map,
            width: width,
            listWidth: width,
            minChars: 2,
            // @ToDo: Restrict to the Country if using a Country config
            //countryString: ,
            emptyText: S3.i18n.gis_search
        });
        toolbar.addSeparator();
        toolbar.add(mapSearch);
    }
    
    // Throbber
    var throbber = new Ext.BoxComponent({
        autoEl: {
            tag: 'img',
            src: S3.gis.ajax_loader
        },
        cls: 'hide',
        id: 'layer_throbber'
    });
    toolbar.add(throbber);
    
    // pass to Global Scope
    S3.gis.toolbar = toolbar;
}
