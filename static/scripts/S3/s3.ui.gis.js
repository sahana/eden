/*
 * Map Widget
 */
(function(factory) {
    'use strict';
    // Use window. for Browser globals (not AMD or Node):
    factory(window.jQuery, window._, window.ol);
})(function($, _, ol) {

    'use strict';
    var mapID = 0;

    $.widget('s3.showMap', {

        /**
         * Options
         */
        options: {
            id: 'default_map',  // Map ID (Div)
            i18n: {'loading': 'Loading',
                   'requires_login': 'Requires Login'
                   },
            //height: 400,        // Map Height (pixels)
            //width: 400,         // Map Width (pixels)
            lat: 0,             // Center Lat
            lon: 0,             // Center Lon
            //projection: 3857,  // EPSG:3857 = Spherical Mercator
            zoom: 0,            // Map Zoom
            layers_osm: []      // OpenStreetMap Layers
        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = mapID;
            mapID += 1;
            this.eventNamespace = '.s3Map';
            this.proxyHost = S3.Ap.concat('/gis/proxy?url=');

        },

        /**
         * Initialize the widget
         */
        _init: function(options) {

            //var el = $(this.element);

            this.refresh();

        },

        /**
          * Remove generated elements & reset other changes
          */
        _destroy: function() {
            $.Widget.prototype.destroy.call(this);
        },

        /**
         * Redraw widget contents
         */
        refresh: function() {
            //this._unbindEvents();
            //this._deserialize();

            var options = this.options;

            // Map views always need a projection
            /*
            var extent = [0, 0, width, height]; // for ImageMap
            var projection = new ol.proj.Projection({
                extent: extent
            });*/

            var layers = this.addLayers();

            var map = new ol.Map({
                layers: layers,
                target: options.id,
                view: new ol.View({
                    center: ol.proj.fromLonLat([options.lon, options.lat]),
                    zoom: options.zoom
                })
            });
            this.map = map;

            // Tooltip
            var tooltip = $('#' + this.options.id + ' .s3-gis-tooltip');
            this.tooltip = tooltip;

            var tooltip_ol = new ol.Overlay({
                element: tooltip[0],
                positioning: 'bottom-center',
                stopEvent: false,
                offset: [0, -15]
            });
            map.addOverlay(tooltip_ol);
            this.tooltip_ol = tooltip_ol;

            //this._serialize();
            this._bindEvents(map);
        },

        /**
         * Add Layers to the Map
         */
        addLayers: function() {
            var layers = [];

            // OpenStreetMap
            this.addLayersOSM(layers);

            // GeoJSON Layers
            this.addLayersGeoJSON(layers);

            return layers;
        },

        /**
         * Add OSM Layers to the Map
         */
        addLayersOSM: function(layers) {
            var attributions,
                base,
                layer,
                layers_osm = this.options.layers_osm || [],
                maxZoom,
                opaque,
                options,
                url;

            for (var i=0; i < layers_osm.length; i++) {

                layer = layers_osm[i];

                if (undefined != layer.attribution) {
                    attributions = [layer.attribution];
                } else {
                    attributions = [ol.source.OSM.ATTRIBUTION];
                }

                if (undefined != layer.maxZoom) {
                    maxZoom = layer.maxZoom;
                } else {
                    maxZoom = 19;
                }

                if (undefined != layer.base) {
                    opaque = layer.base;
                } else {
                    opaque = true;
                }

                if (undefined != layer.url) {
                    url = layer.url;
                } else {
                    url = 'https://{a-c}.tile.openstreetmap.org/{z}/{x}/{y}.png';
                }

                options = {attributions: attributions,
                           maxZoom: maxZoom,
                           opaque: opaque,
                           url: url
                           }
                layers.push(new ol.layer.Tile({
                                source: new ol.source.OSM(options)
                            }));
            }
        },

        /**
         * Add GeoJSON Layers to the Map
         *
         * @ToDo: Combine these 7 layer types server-side to save a little bandwidth
         */
        addLayersGeoJSON: function(layers) {
            var options = this.options,
                feature_queries = options.feature_queries || [],
                feature_resources = options.feature_resources || [],
                format,
                layer,
                layerType,
                layers_feature = options.layers_feature || [],
                layers_geojson = options.layers_geojson || [],
                layers_georss = options.layers_georss || [],
                layers_shapefile = options.layers_shapefile || [],
                layers_theme = options.layers_theme || [],
                s3_popup_format,
                style,
                url,
                vectorLayer,
                vectorLayers = [],
                vectorSource;

            vectorLayers = feature_queries.concat(feature_resources)
                                          .concat(layers_feature)
                                          .concat(layers_geojson)
                                          .concat(layers_georss)
                                          .concat(layers_shapefile)
                                          .concat(layers_theme);

            for (var i=0; i < vectorLayers.length; i++) {

                layer = vectorLayers[i];

                if (undefined != layer.projection) {
                    format = new ol.format.GeoJSON({dataProjection: 'EPSG:' + layer.projection});
                } else {
                    // Feature Layers, GeoRSS & KML are always in 4326
                    format = new ol.format.GeoJSON({dataProjection: 'EPSG:4326'});
                }

                style = this.layerStyle(layer);

                url = layer.url;
                /* @ToDo: Optimise by not xferring appname
                if (!url.startsWith('http')) {
                    // Feature Layer read from this server
                    url = S3.Ap.concat(url);
                } */

                vectorSource = new ol.source.Vector({
                    url: url,
                    format: format
                });

                vectorLayer = new ol.layer.Vector({
                    source: vectorSource,
                    style: style
                });

                // Set the popup_format, even if empty
                // - leave if not set (e.g. Feature Queries)
                if (undefined != layer.popup_format) {
                    vectorLayer.s3_popup_format = layer.popup_format;
                }

                if (undefined != layer.type) {
                    layerType = layer.type;
                } else {
                    // Feature Layers
                    layerType = 'feature';
                }
                vectorLayer.s3_layer_type = layerType;

                layers.push(vectorLayer);
            }
        },

        /**
         * Style a Vector Layer
         */
        layerStyle: function(layer) {

            var style;

            if (undefined !== layer.marker) {
                // Style all features with layer.marker
                style = new ol.style.Style({
                    image: new ol.style.Icon({
                        // @ToDo: Allow external markers prefixed by http
                        // @ToDo: Optimise Marker for ol6 by not xferring the h/w
                        src: S3.Ap.concat('/static/img/markers/' + layer.marker.i)
                    })
                });
            } else if (undefined !== layer.marker) {
                // Style features using layer.style
                style = layer.style;
            } else {
                // Default Style
                var fill = new ol.style.Fill({
                    color: 'rgba(255,255,255,0.4)'
                });
                var stroke = new ol.style.Stroke({
                    color: '#3399CC',
                    width: 1.25
                });
                var image = new ol.style.Icon({
                    src: S3.Ap.concat('/static/img/markers/' + this.options.marker)
                })
                var styles = {
                    'Point': new ol.style.Style({
                        image: image
                    }),
                    'LineString': new ol.style.Style({
                        stroke: stroke
                    }),
                    'MultiLineString': new ol.style.Style({
                        stroke: stroke
                    }),
                    'MultiPoint': new ol.style.Style({
                        image: image
                    }),
                    'MultiPolygon': new ol.style.Style({
                        stroke: stroke,
                        fill: fill
                    }),
                    'Polygon': new ol.style.Style({
                        stroke: stroke,
                        fill: fill
                    }),
                    'GeometryCollection': new ol.style.Style({
                        stroke: stroke,
                        fill: fill,
                        image: image
                    }),
                    'Circle': new ol.style.Style({
                        stroke: stroke,
                        fill: fill
                    })
                };
                style = function(feature) {
                    return styles[feature.getGeometry().getType()];
                };
            }
            return style;

        },

        /**
         * Add a Popup to map
         */
        addPopup: function(feature, layer, url, content, iframe) {
            var map = this.map,
                id = this.id + '_' + layer.ol_uid + '_' + feature.get('id') + '_popup';
            if (iframe && url) {
                if (url.indexOf('http://') === 0 ) {
                    // Use Proxy for remote popups
                    url = this.proxyHost + encodeURIComponent(url);
                }
                content = '<iframe src="' + url + '" onload="S3.gis.popupLoaded(\'' + id + '\')" class="loading" marginWidth="0" marginHeight="0" frameBorder="0"></iframe>';
            } else if (undefined == content) {
                content = this.options.i18n.loading + '...<div class="throbber"></div>';
            }
            $('#' + this.options.id).append('<div id="' + id + '" class="s3-gis-popup"><div class="s3-gis-popup-close"></div><div class="s3-gis-popup-content"></div></div>')
            var popup = $('#' + id),
                popup_ol = new ol.Overlay({
                element: popup[0],
                positioning: 'bottom-center',
                //stopEvent: false,
                offset: [0, -12]
            });
            map.addOverlay(popup_ol);
            var coordinates = feature.getGeometry().getCoordinates();
            popup_ol.setPosition(coordinates);
            $('#' + id + ' .s3-gis-popup-content').html(content);
            popup.show();
            $('#' + id + ' .s3-gis-popup-close').on('click', {id: id, map: map, overlay: popup_ol}, this.removePopup);
            if (!iframe && undefined != url) {
                // use AJAX to get the contentHTML
                this._loadDetails(url, id, popup);
            }
            //return popup;
        },

        /**
         * Remove a Popup
         */
        removePopup: function(e) {
            e.data.map.removeOverlay(e.data.overlay);
            $('#' + e.data.id).remove();
            e.preventDefault();
        },

        /**
         * Load the Popup Details via AJAX
         * - used by addPopup and map.on('click')
         */
        _loadDetails: function(url, id, popup) {
            var self = this;
            if (url.indexOf('http://') === 0) {
                // Use Proxy for remote popups
                url = this.proxyHost + encodeURIComponent(url);
            }
            // @ToDo: Support option to load just a section of the page
            // e.g. USGS would just load '#main'
            /*
            url_parts = url.split('?', 1);
            url = url_parts[0];
            url = url + ' #main';
            $('#' + id).load(url, url_parts[1], function() {
                popup.updateSize();
            });*/
            $.ajaxS3({
                url: url,
                dataType: 'html',
                // gets moved to 'done' inside AjaxS3
                success: function(data) {
                    try {
                        // Load response into div
                        $('#' + id + ' .s3-gis-popup-content').html(data);
                        //popup.updateSize();
                        // Resize when images are loaded
                        //popup.registerImageListeners();
                        // Check for links to load in iframe
                        $('#' + id + ' a.btn.iframe').click(function() {
                            var url = $(this).attr('href');
                            if (url.indexOf('http://') === 0) {
                                // Use Proxy for remote popups
                                url = self.proxyHost + encodeURIComponent(url);
                            }
                            var content = '<iframe src="' + url + '" onload="S3.gis.popupLoaded(\'' + id + '\')" class="loading" marginWidth="0" marginHeight="0" frameBorder="0"></iframe>';
                            $('#' + id + ' .s3-gis-popup-content').html(content);
                            // Prevent default
                            return false;
                        });
                    } catch(e) {
                        // Page is probably trying to load 'local' resources from us
                        // @ToDo: Load in iframe instead...
                    }
                },
                // gets moved to 'fail' inside AjaxS3
                error: function(jqXHR, textStatus, errorThrown) {
                    if (errorThrown == 'UNAUTHORIZED') {
                        msg = self.options.i18n.requires_login;
                    } else {
                        msg = jqXHR.responseText;
                    }
                    $('#' + id + ' .s3-gis-popup-content').html(msg);
                    //popup.updateSize();
                }
            });
        },


        /**
         * Encode this.data as JSON and write into real input
         *
         * (unused)
         *
         * @returns {JSON} the JSON data
         *
        _serialize: function() {

            var json = JSON.stringify(this.data);
            $(this.element).val(json);
            return json;

        },*/

        /**
         * Parse the JSON from real input into this.data
         *
         * (unused)
         *
         * @returns {object} this.data
         */
        _deserialize: function() {

            //var value = $(this.element).val() || '{}';
            //this.data = JSON.parse(value);
            //return this.data;

        },

        /**
         * Bind event handlers (after refresh)
         *
         */
        _bindEvents: function(map) {

            var self = this,
                //ns = this.eventNamespace,
                attributes,
                content,
                coordinates,
                defaults,
                feature,
                key,
                keys,
                layer,
                popup_format,
                results,
                template;

            // Show Tooltip when hovering over marker
            map.on('pointermove', function(e) {
                if (e.dragging) {
                    self.tooltip.hide();
                    return;
                }
                results = map.forEachFeatureAtPixel(e.pixel, function(feature, layer) {
                    return {feature: feature,
                            layer: layer
                            };
                });
                if (results) {
                    feature = results.feature;
                    layer = results.layer;
                    coordinates = feature.getGeometry().getCoordinates();
                    self.tooltip_ol.setPosition(coordinates);

                    if (undefined != layer.s3_popup_format) {
                        // GeoJSON Feature Layers
                        _.templateSettings = {interpolate: /\{(.+?)\}/g};
                        popup_format = layer.s3_popup_format;
                        template = _.template(popup_format);
                        // Ensure we have all keys (we don't transmit empty attr)
                        attributes = {};//= feature.getProperties()
                        defaults = {};
                        keys = popup_format.split('{');
                        for (var i = 0; i < keys.length; i++) {
                            key = keys[i].split('}')[0];
                            attributes[key] = feature.get(key);
                            defaults[key] = '';
                        }
                        _.defaults(attributes, defaults);
                        content = template(attributes);
                    } else if (undefined != attributes.popup) {
                        // Feature Queries or Theme Layers
                        content = feature.get('popup');
                    } else if (undefined != feature.get('name')) {
                        // GeoJSON, GeoRSS or Legacy Features
                        content = feature.get('name');
                    } else if (undefined != layer.title) {
                        // KML or WFS
                        var a = feature.get(layer.title);
                        var type = typeof a;
                        if ('object' == type) {
                            content = a.value;
                        } else {
                            content = a;
                        }
                    }

                    self.tooltip.html(content).show();

                } else {
                    self.tooltip.hide();
                }
            });

            // Show Popup when clicking on a marker
            map.on('click', function(e) {
                results = map.forEachFeatureAtPixel(e.pixel, function(feature, layer) {
                    return {feature: feature,
                            layer: layer
                            };
                });
                if (results) {
                    // Close the tooltip
                    self.tooltip.hide();

                    feature = results.feature;
                    layer = results.layer;

                    // @ToDo: Style the feature as highlighted
                    // irrevant for icon-based styles?
                    // easy to apply a default here, but how to action based on custom styles? Just reduce Opacity?

                    // @ToDo: Handle Clusters

                    // Single Feature
                    var attributes = feature.getProperties(),
                        content,
                        data_link,
                        layerType = layer.s3_layer_type,
                        popup_url;

                    if (layerType == 'kml') {
                        var titleField;
                        if (undefined != layer.title) {
                            titleField = layer.title;
                        } else {
                            titleField = 'name';
                        }
                        if (undefined != feature.style.balloonStyle) {
                            // Use the provided BalloonStyle
                            var balloonStyle = feature.style.balloonStyle;
                            // "<strong>{name}</strong><br /><br />{description}"
                            content = balloonStyle.replace(/{([^{}]*)}/g,
                                function (a, b) {
                                    var r = attributes[b];
                                    return typeof r === 'string' || typeof r === 'number' ? r : a;
                                }
                            );
                        } else {
                            // Build the Popup contents manually
                            var type = typeof attributes[titleField];
                            var title;
                            if ('object' == type) {
                                title = attributes[titleField].value;
                            } else {
                                title = attributes[titleField];
                            }
                            content = '<h3>' + title + '</h3>';
                            var body = layer.body.split(' ');
                            var label, row, value;
                            for (var j = 0; j < body.length; j++) {
                                type = typeof attributes[body[j]];
                                if ('object' == type) {
                                    // Geocommons style
                                    label = attributes[body[j]].displayName;
                                    if (label === '') {
                                        label = body[j];
                                    }
                                    value = attributes[body[j]].value;
                                    row = '<div class="gis_popup_row"><div class="gis_popup_label">' + label +
                                          ':</div><div class="gis_popup_cell">' + value + '</div></div>';
                                } else if (undefined != attributes[body[j]]) {
                                    row = '<div class="gis_popup_row">' + attributes[body[j]] + '</div>';
                                } else {
                                    // How would we get here?
                                    row = '';
                                }
                                content += row;
                            }
                        }
                        // Protect the content against JavaScript attacks
                        if (content.search('<script') != -1) {
                            content = 'Content contained Javascript! Escaped content below.<br />' + content.replace(/</g, '<');
                        }
                    } else if (layerType == 'gpx') {
                        // @ToDo: display as many attributes as we can: Description (Points), Date, Author?, Lat, Lon
                    } else if ((layerType == 'shapefile') || (layerType == 'geojson')) {
                        // We don't have control of attributes, so simply display all
                        // @ToDo: have an optional style.popup (like KML's balloonStyle)
                        content = '<div>';
                        var label, prop, row, value;
                        $.each(attributes, function(label, value) {
                            if (label == 'id_orig') {
                                label = 'id';
                            }
                            row = '<div class="gis_popup_row"><div class="gis_popup_label">' + label +
                                  ':</div><div class="gis_popup_cell">' + value + '</div></div>';
                            content += row;
                        });
                        content += '</div>';
                    } else if (layerType == 'wfs') {
                        var titleField;
                        if (undefined != layer.title) {
                            titleField = layer.title;
                        } else {
                            titleField = 'name';
                        }
                        var title = attributes[titleField];
                        content = '<h3>' + title + '</h3>';
                        var row;
                        $.each(attributes, function(label, value) {
                            row = '<div class="gis_popup_row"><div class="gis_popup_label">' + label +
                                  ':</div><div class="gis_popup_val">' + value + '</div></div>';
                            content += row;
                        });
                    } else {
                        // @ToDo: disambiguate these by type
                        if (undefined != attributes.url) {
                            // Feature Query with Popup contents pulled via AJAX
                            popup_url = attributes.url;
                            // Defaulted within addPopup()
                            //content = i18n.loading + "...<div class='throbber'></div>";
                        } else if (undefined != layer.s3_url_format) {
                            // Feature Layer or Feature Resource
                            // Popup contents are pulled via AJAX
                            _.templateSettings = {interpolate: /\{(.+?)\}/g};
                            //var s3_url_format = layer.s3_url_format;
                            var template = _.template(layer.s3_url_format);
                            // Ensure we have all keys (we don't transmit empty attr)
                            /* Only needed once we start getting non-id formats
                            var defaults = {},
                                key,
                                keys = s3_popup_format.split('{');
                            for (var j = 0; j < keys.length; j++) {
                                key = keys[j].split('}')[0];
                                defaults[key] = '';
                            }
                            _.defaults(attributes, defaults);*/
                            // Since this is single feature case, feature should have single id
                            if (attributes.id.constructor === Array) {
                                attributes.id = attributes.id[0];
                            }
                            popup_url = template(attributes);
                        } else {
                            // Popup contents are built from the attributes
                            if (undefined == attributes.name) {
                                name = '';
                            } else {
                                name = '<h3>' + attributes.name + '</h3>';
                            }
                            var description;
                            if (undefined == attributes.description) {
                                description = '';
                            } else {
                                description = '<p>' + attributes.description + '</p>';
                            }
                            var link;
                            if (undefined == attributes.link) {
                                link = '';
                            } else {
                                link = '<a href="' + attributes.link + '" target="_blank">' + attributes.link + '</a>';
                            }
                            var data;
                            if (undefined == attributes.data) {
                                data = '';
                            } else if (attributes.data.indexOf('http://') === 0) {
                                data_link = true;
                                var data_id = S3.uid();
                                data = '<div id="' + data_id + '">' + self.options.i18n.loading + "...<div class='throbber'></div>" + '</div>';
                            } else {
                                data = '<p>' + attributes.data + '</p>';
                            }
                            var image;
                            if (undefined == attributes.image) {
                                image = '';
                            } else if (attributes.image.indexOf('http://') === 0) {
                                image = '<img src="' + attributes.image + '" height=300 width=300>';
                            } else {
                                image = '';
                            }
                            content = name + description + link + data + image;
                        }
                    }
                    var popup = self.addPopup(feature, layer, popup_url, content);
                    if (data_link) {
                        // call AJAX to get the linked data
                        self._loadDetails(attributes.data, data_id, popup);
                    }
                }
            });

        },

        /**
         * Unbind events (before refresh)
         *
         * (unused)
         */
        _unbindEvents: function() {

            //var ns = this.eventNamespace;

            return true;
        }

    });
});
