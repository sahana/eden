
import unittest

class TrueCodePaths(unittest.TestCase):
    def setUp(self):
        vars = request.vars
        vars["lat"] = 0
        vars["lon"] = 0
        vars["zoom"] = 1
                
        self.old_s3roles = list(session.s3.roles)
        session.s3.roles.append(1)
        
    def tearDown(self):
        vars = request.vars
        del vars["lat"]
        del vars["lon"]
        del vars["zoom"]
        session.s3.roles = self.old_s3roles
        
    def check(test, scripts):
        expected = [
            "S3.public_url = 'http://127.0.0.1:8000';",
            "S3.gis.mapAdmin = true;",
            "S3.gis.window = true;",
            "S3.gis.windowHide = true;",
            "S3.gis.west_collapsed = true;",
            "S3.gis.map_height = 123;",
            "S3.gis.map_width = 123;",
            "S3.gis.zoom = 1;",
            "S3.gis.lat, S3.gis.lon;",
            "S3.gis.bottom_left = new OpenLayers.LonLat(-10.000000, -10.000000);",
            "S3.gis.top_right = new OpenLayers.LonLat(10.000000, 10.000000);",
            "S3.gis.projection = '900913';",
            "S3.gis.units = 'm';",
            "S3.gis.maxResolution = 156543.033900;",
            "S3.gis.maxExtent = new OpenLayers.Bounds(-20037508, -20037508, 20037508, 20037508.34);",
            "S3.gis.numZoomLevels = 22;",
            "S3.gis.max_w = 30;",
            "S3.gis.max_h = 35;",
            "S3.gis.mouse_position = 'mgrs';",
            "S3.gis.wms_browser_name = 'Test WMS browser';",
            "S3.gis.wms_browser_url = 'test%3A//test_WMS_URL';",
            "S3.gis.draw_feature = 'inactive';",
            "S3.gis.draw_polygon = 'inactive';",
            "S3.gis.marker_default = 'gis_marker.image.marker_red.png';",
            "S3.gis.marker_default_height = 34;",
            "S3.gis.marker_default_width = 20;",
            "S3.i18n.gis_legend = 'Legend';",
            "S3.i18n.gis_search = 'Search Geonames';",
            "S3.i18n.gis_search_no_internet = 'Geonames.org search requires Internet connectivity!';",
            "S3.i18n.gis_requires_login = 'Requires Login';",
            "S3.i18n.gis_base_layers = 'Base Layers';",
            "S3.i18n.gis_overlays = 'Overlays';",
            "S3.i18n.gis_layers = 'Layers';",
            "S3.i18n.gis_draft_layer = 'Draft Features';",
            "S3.i18n.gis_cluster_multiple = 'There are multiple records at this location';",
            "S3.i18n.gis_loading = 'Loading';",
            "S3.i18n.gis_length_message = 'The length is';",
            "S3.i18n.gis_area_message = 'The area is';",
            "S3.i18n.gis_length_tooltip = 'Measure Length: Click the points along the path & end with a double-click';",
            "S3.i18n.gis_area_tooltip = 'Measure Area: Click the points around the polygon & end with a double-click';",
            "S3.i18n.gis_zoomfull = 'Zoom to maximum map extent';",
            "S3.i18n.gis_zoomout = 'Zoom Out: click in the map or use the left mouse button and drag to create a rectangle';",
            "S3.i18n.gis_zoomin = 'Zoom In: click in the map or use the left mouse button and drag to create a rectangle';",
            "S3.i18n.gis_pan = 'Pan Map: keep the left mouse button pressed and drag the map';",
            "S3.i18n.gis_navPrevious = 'Previous View';",
            "S3.i18n.gis_navNext = 'Next View';",
            "S3.i18n.gis_geoLocate = 'Zoom to Current Location';",
            "S3.i18n.gis_draw_feature = 'Add Point';",
            "S3.i18n.gis_draw_polygon = 'Add Polygon';",
            "S3.i18n.gis_save = 'Save: Default Lat, Lon & Zoom for the Viewport';",
            "S3.i18n.gis_potlatch = 'Edit the OpenStreetMap data for this area';",
            "S3.i18n.gis_current_location = 'Current Location';",
            """if (typeof(printCapabilities) != 'undefined') {
            // info.json from script headers OK
            printProvider = new GeoExt.data.PrintProvider({
                //method: 'POST',
                //url: 'test_print_script_url/',
                method: 'GET', // 'POST' recommended for production use
                capabilities: printCapabilities, // from the info.json returned from the script headers
                customParams: {
                    mapTitle: 'Test Map Title',
                    subTitle: 'Printed from Sahana Eden',
                    creator: ''
                }
            });
            // Our print page. Stores scale, center and rotation and gives us a page
            // extent feature that we can add to a layer.
            printPage = new GeoExt.data.PrintPage({
                printProvider: printProvider
            });

            //var printExtent = new GeoExt.plugins.PrintExtent({
            //    printProvider: printProvider
            //});
            // A layer to display the print page extent
            //var pageLayer = new OpenLayers.Layer.Vector('Print Extent');
            //pageLayer.addFeatures(printPage.feature);
            //pageLayer.setVisibility(false);
            //map.addLayer(pageLayer);
            //var pageControl = new OpenLayers.Control.TransformFeature();
            //map.addControl(pageControl);
            //map.setOptions({
            //    eventListeners: {
                    // recenter/resize page extent after pan/zoom
            //        'moveend': function() {
            //            printPage.fit(mapPanel, true);
            //        }
            //    }
            //});
            // The form with fields controlling the print output
            S3.gis.printFormPanel = new Ext.form.FormPanel({
                title: 'Print Map',
                rootVisible: false,
                split: true,
                autoScroll: true,
                collapsible: true,
                collapsed: true,
                collapseMode: 'mini',
                lines: false,
                bodyStyle: 'padding:5px',
                labelAlign: 'top',
                defaults: {anchor: '100%%'},
                listeners: {
                    'expand': function() {
                        //if (null == mapPanel.map.getLayersByName('Print Extent')[0]) {
                        //    mapPanel.map.addLayer(pageLayer);
                        //}
                        if (null == mapPanel.plugins[0]) {
                            //map.addLayer(pageLayer);
                            //pageControl.activate();
                            //mapPanel.plugins = [ new GeoExt.plugins.PrintExtent({
                            //    printProvider: printProvider,
                            //    map: map,
                            //    layer: pageLayer,
                            //    control: pageControl
                            //}) ];
                            //mapPanel.plugins[0].addPage();
                        }
                    },
                    'collapse':  function() {
                        //mapPanel.map.removeLayer(pageLayer);
                        //if (null != mapPanel.plugins[0]) {
                        //    map.removeLayer(pageLayer);
                        //    mapPanel.plugins[0].removePage(mapPanel.plugins[0].pages[0]);
                        //    mapPanel.plugins = [];
                        //}
                    }
                },
                items: [{
                    xtype: 'textarea',
                    name: 'comment',
                    value: '',
                    fieldLabel: 'Comment',
                    plugins: new GeoExt.plugins.PrintPageField({
                        printPage: printPage
                    })
                }, {
                    xtype: 'combo',
                    store: printProvider.layouts,
                    displayField: 'name',
                    fieldLabel: 'Layout',
                    typeAhead: true,
                    mode: 'local',
                    triggerAction: 'all',
                    plugins: new GeoExt.plugins.PrintProviderField({
                        printProvider: printProvider
                    })
                }, {
                    xtype: 'combo',
                    store: printProvider.dpis,
                    displayField: 'name',
                    fieldLabel: 'Resolution',
                    tpl: '<tpl for="."><div class="x-combo-list-item">{name} dpi</div></tpl>',
                    typeAhead: true,
                    mode: 'local',
                    triggerAction: 'all',
                    plugins: new GeoExt.plugins.PrintProviderField({
                        printProvider: printProvider
                    }),
                    // the plugin will work even if we modify a combo value
                    setValue: function(v) {
                        v = parseInt(v) + ' dpi';
                        Ext.form.ComboBox.prototype.setValue.apply(this, arguments);
                    }
                //}, {
                //    xtype: 'combo',
                //    store: printProvider.scales,
                //    displayField: 'name',
                //    fieldLabel: 'Scale',
                //    typeAhead: true,
                //    mode: 'local',
                //    triggerAction: 'all',
                //    plugins: new GeoExt.plugins.PrintPageField({
                //        printPage: printPage
                //    })
                //}, {
                //    xtype: 'textfield',
                //    name: 'rotation',
                //    fieldLabel: 'Rotation',
                //    plugins: new GeoExt.plugins.PrintPageField({
                //        printPage: printPage
                //    })
                }],
                buttons: [{
                    text: 'Create PDF',
                    handler: function() {
                        // the PrintExtent plugin is the mapPanel's 1st plugin
                        //mapPanel.plugins[0].print();
                        // convenient way to fit the print page to the visible map area
                        printPage.fit(mapPanel, true);
                        // print the page, including the legend, where available
                        if (null == legendPanel) {
                            printProvider.print(mapPanel, printPage);
                        } else {
                            printProvider.print(mapPanel, printPage, {legend: legendPanel});
                        }
                    }
                }]
            });
        } else {
            // Display error diagnostic
            S3.gis.printFormPanel = new Ext.Panel ({
                title: 'Print Map',
                rootVisible: false,
                split: true,
                autoScroll: true,
                collapsible: true,
                collapsed: true,
                collapseMode: 'mini',
                lines: false,
                bodyStyle: 'padding:5px',
                labelAlign: 'top',
                defaults: {anchor: '100%'},
                html: 'Printing disabled since server not accessible: <BR />test_print_script_url/'
            });
        }"""
        ]
        test_gis = s3base.GIS()
        actual_output = str(
            test_gis.show_map(
                projection = 900913,
                height = 123,
                width = 123,
                bbox = dict(
                    max_lat= 10,
                    min_lat= -10,
                    max_lon= 10,
                    min_lon= -10
                ),
                legend = "Test",
                add_feature = True,
                add_polygon = True,
                window = True,
                closable = True,
                mouse_position = "mgrs",
                wms_browser = {
                    "name": "Test WMS browser",
                    "url": "test://test_WMS_URL"
                },
                print_tool = {
                    "url": "test_print_script_url/",
                    "subTitle": "Tested from TestS3GIS",
                     # looks like a bug: "mapTitle" vs "title"
                    "title": "Test print tool",
                    "mapTitle": "Test Map Title"
                },
                collapsed = True,
                window_hide = True,
                catalogue_toolbar = True,
                toolbar = True,
                search = True,
                catalogue_layers = True,
                zoom = 1,
            )
        )
        for expected_line in expected:
            assert expected_line in actual_output
        
        substitutions = dict(application_name = request.application)
        for script in scripts:
            script_string = "<script src=\"%s\" type=\"text/javascript\"></script>" % (
                script % substitutions
            )
            assert script_string in actual_output

    def test_true_code_paths_with_debug(self):
        current.session.s3.debug = True
        self.check(
            scripts = (
                "/%(application_name)s/static/scripts/gis/usng2.js",
                "/%(application_name)s/static/scripts/gis/MP.js",
                "/%(application_name)s/static/test_print_script_url/info.json?var=printCapabilities",
            )
        )

    def test_true_code_paths(self):
        "Basic map with true code paths turned on"
        current.session.s3.debug = False
        self.check(
            scripts = (
                "/%(application_name)s/static/test_print_script_url/info.json?var=printCapabilities",
                "/%(application_name)s/static/scripts/gis/MGRS.min.js",
            )
        )

