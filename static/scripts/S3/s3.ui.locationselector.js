/**
 * jQuery UI LocationSelector Widget
 *
 * @copyright 2014 (c) Sahana Software Foundation
 * @license MIT
 *
 * requires jQuery 1.9.1+
 * requires jQuery UI 1.10 widget factory
 * requires jQuery jstree 3.0.3
 */
(function($, undefined) {

    "use strict";
    var locationselectorID = 0;

    // Global cache for location data (shared with other location selectors)
    var hierarchyLocations = {},
        hierarchyLabels = {};

    /**
     * LocationSelector widget
     */
    $.widget('s3.locationselector', {

        /**
         * Default options
         *
         * @prop {bool} hideLx - hide Lx selectors until parent Lx has been
         *                       selected (progressive revelation)
         * @prop {bool} reverseLx - render Lx selectors in reverse order below
         *                          address fields
         * @prop {object} locations - initial location hierarchy data
         * @prop {object} labels - initial hierarchy labels per L0
         */
        options: {
            hideLx: true,
            reverseLx: false,

            locations: null,
            labels: null
        },

        /**
         * Create the widget
         */
        _create: function() {

            var el = $(this.element);

            this.id = locationselectorID;
            locationselectorID += 1;

            // Namespace for events
            this.namespace = '.locationselector';
        },

        /**
         * Update the widget options
         */
        _init: function() {

            // Element to initialize on is the (hidden) real input
            var el = $(this.element),
                opts = this.options;

            // Base selector is required
            var fieldname = el.attr('id');
            if (!fieldname) {
                throw 'Location selector widget: real input field without id';
            }

            this.fieldname = fieldname;
            this.input = el;

            // Initialize data dict
            this.data = null;

            // Store hierarchy data passed with options in global cache
            this._storeHierarchyData(opts.labels, opts.locations);

            this.refresh();
        },

        /**
         * Remove generated elements & reset other changes
         */
        _destroy: function() {

            $.Widget.prototype.destroy.call(this);
        },

        /**
         * Redraw contents
         */
        refresh: function() {

            this._unbindEvents();

            // Read the data from real input
            var data = this._deserialize();

            // Render the widget
            this._renderWidget();

            var selector = '#' + this.fieldname;

            // Should we use the Geocoder?
            if ($(selector + '_geocode button').length) {
                this.useGeocoder = true;
            } else {
                this.useGeocoder = false;
            }

            // Populate L0 selector (if present)
            // @todo: do this only if dropdown is empty
            var row = $(selector + '_L0__row');
            if (row.length) {
                var locations = [],
                    location,
                    locationID;
                // Get all L0 locations from global cache
                for (locationID in hierarchyLocations) {
                    location = hierarchyLocations[locationID];
                    if (location['l'] === 0) {
                        location['i'] = locationID;
                        locations.push(location);
                    }
                }
                // Sort locations by name
                locations.sort(function(a, b) {
                   return a.n.localeCompare(b.n);
                });
                // Populate dropdown
                var dropdown = $(selector + '_L0'),
                    option;
                for (var i=0, len=locations.length; i < len; i++) {
                    location = locations[i];
                    locationID = location['i'];
                    option = '<option value="' + locationID + '">' + location['n'] + '</option>';
                    dropdown.append(option);
                }
                // Show the L0 row
                row.removeClass('hide').show();
                // Handle separate label row in tuple themes
                var labelRow = $(selector + '_L0__row1');
                if (labelRow.length) {
                    labelRow.removeClass('hide').show();
                }
            }

            // Propagate pre-selected values
            var L0 = data.L0,
                L1 = data.L1,
                L2 = data.L2,
                L3 = data.L3,
                L4 = data.L4,
                L5 = data.L5;
            if (L0) {
                this._lxSelect(0, L0, true);
            }
            // || is to support Missing levels
            if (L1 || L2) {
                this._lxSelect(1, L1 || L2, true);
            }
            if (L2 || L3) {
                this._lxSelect(2, L2 || L3, true);
            }
            if (L3 || L4) {
                this._lxSelect(3, L3 || L4, true);
            }
            if (L4 || L5) {
                this._lxSelect(4, L4 || L5, true);
            }
            if (L5) {
                this._lxSelect(5, L5, true);
            }

            // Show Address/Postcode Rows (__row1 = tuple themes)
            $(selector + '_address').val(data.address);
            $(selector + '_address__row').removeClass('hide').show();
            $(selector + '_address__row1').removeClass('hide').show();

            $(selector + '_postcode').val(data.postcode);
            $(selector + '_postcode__row').removeClass('hide').show();
            $(selector + '_postcode__row1').removeClass('hide').show();

            // Show Map icon
            $(selector + '_map_icon__row').removeClass('hide').show();
            if (data.lat || data.lon || data.wkt) {
                // Don't do a Geocode when reading the data
                this.input.data('manually_geocoded', true);
                this._showMap();
            } else {
                this._hideMap();
            }

            // Bind event handlers
            this._bindEvents();
        },

        /**
         * Render the widget components
         *
         * @todo: adapt for inline-forms
         */
        _renderWidget: function() {

            var fieldname = this.fieldname;
            var selector = '#' + fieldname,
                reverseLx = this.options.reverseLx;

            // Set ID for map wrapper
            var mapWrapper = $(selector + '_map_icon__row .map_wrapper');
            mapWrapper.attr('id', this.fieldname + '_map_wrapper');

            // Arrange the widget's inner elements
            var formRow = $(selector + '__row'),
                errorWrapper = this.input.next('.error_wrapper'),
                mapIconRow = $(selector + '_map_icon__row'),
                L0Row = $(selector + '_L0__row'),
                postcodeRow = $(selector + '_postcode__row');
            if (formRow.is('.control-group, .form-row')) {
                // Bootstrap/Foundation formstyle:
                // Move the visible rows underneath the real (hidden) one
                var L1Row = $(selector + '_L1__row');
                var L2Row = $(selector + '_L2__row');
                var L3Row = $(selector + '_L3__row');
                var L4Row = $(selector + '_L4__row');
                var L5Row = $(selector + '_L5__row');
                var addressRow = $(selector + '_address__row');
                if (reverseLx) {
                    formRow.hide()
                           .after(mapWrapper)
                           .after(mapIconRow)
                           .after(L0Row)
                           .after(L1Row)
                           .after(L2Row)
                           .after(L3Row)
                           .after(L4Row)
                           .after(L5Row)
                           .after(postcodeRow)
                           .after(addressRow)
                           .after(errorWrapper);
                } else {
                    formRow.hide()
                           .after(mapWrapper)
                           .after(mapIconRow)
                           .after(postcodeRow)
                           .after(addressRow)
                           .after(L5Row)
                           .after(L4Row)
                           .after(L3Row)
                           .after(L2Row)
                           .after(L1Row)
                           .after(L0Row)
                           .after(errorWrapper);
                }
            } else if (formRow.parent().is('.inline-form')) {
                formRow.show();
            } else {
                // Other formstyle:
                // Hide the main row & move out the Error
                $(selector + '__row1').hide(); // Tuple themes
                formRow.hide().after(errorWrapper);
                if (reverseLx) {
                    L0Row.after(mapWrapper)
                         .after(mapIconRow);
                } else {
                    postcodeRow.after(mapWrapper)
                               .after(mapIconRow);
                }
            }

            // Make errorWrapper clickable to remove it
            if (errorWrapper.length) {
                errorWrapper.one('click' + this.namespace, function() {
                    var $this = $(this);
                    $this.fadeOut('slow', function() {
                        $this.remove();
                    });
                });
            }
        },

        /**
         * An Lx dropdown has been selected
         * - either manually or through an initial value
         *
         * @param {number} level - the Lx level (0..5)
         * @param {number} id - the record ID of the selected Lx location
         * @param {bool} refresh - whether this called before user input
         *                         (in which case we do want to prevent geocoding)
         */
        _lxSelect: function(level, id, refresh) {

            var selector = '#' + this.fieldname,
                opts = this.options;

            var dropdown = $(selector + '_L' + level);

            if (id) {
                // Set this dropdown to this value
                // - this is being set from outside the dropdown, e.g. an
                //   update form or using a visible default location
                dropdown.val(id);
                if (dropdown.hasClass('multiselect') && dropdown.multiselect('instance')) {
                    dropdown.multiselect('refresh');
                }
            } else {
                // Read the selected value from the dropdown
                id = parseInt(dropdown.val());
            }

            // Update hierarchy labels
            if (level === 0) {

                var labels = this._readLabels(id),
                    defaultLabels = hierarchyLabels['d'],
                    levels = ['1', '2', '3', '4', '5'],
                    label,
                    labelHTML,
                    i,
                    s,
                    l;

                for (i=0; i < 5; i++) {

                    l = levels[i];

                    // Use default labels as fallback if no specific label
                    label = labels[l] || defaultLabels[l];

                    s = selector + '_L' + l;
                    dropdown = $(s);

                    // Mark required?
                    // @ToDo: Client-side s3_mark_required function
                    if (dropdown.hasClass('required')) {
                        labelHTML = '<div>' + label + ':<span class="req"> *</span></div>';
                    } else {
                        labelHTML = label + ':';
                    }

                    // Update the label
                    $(s + '__row label').html(labelHTML);
                    // Tuple themes (@todo: why would row1 have a label?)
                    $(s + '__row1 label').html(labelHTML);
                    // Update the placeholder-option in the selector
                    $(s + ' option[value=""]').html(i18n.select + ' ' + label);

                    // Refresh MultiSelect after label change
                    if (dropdown.hasClass('multiselect') && dropdown.multiselect('instance')) {
                        dropdown.multiselect('refresh');
                    }
                }
            }

            // Hide all lower levels & remove their values
            var hideLx = opts.hideLx;
            for (l = level + 1; l < 6; l++) {
                s = selector + '_L' + l;
                if (hideLx) {
                    $(s + '__row').hide();
                    $(s + '__row1').hide(); // Tuple themes
                } else {
                    // Hide the limited options
                    $(s + ' option').remove('[value != ""]');
                    // @ToDo: Read the full set of options via a new call
                }
                $(s).val('');
            }

            if (id) {
                // Show next dropdown
                var next = level + 1;
                var dropdown_row = $(selector + '_L' + next + '__row');

                if (dropdown_row.length) {

                    // Do we need to read hierarchy?
                    var locations,
                        location,
                        locationID;
                    if ($(selector + '_L' + level + ' option[value="' + id + '"]').hasClass('missing')) {
                        // Missing level: we already have the data
                        location = hierarchyLocations[id];
                        location.i = id;
                        locations = [location];
                    } else {
                        var read = true;
                        for (locationID in hierarchyLocations) {
                            if (hierarchyLocations[locationID].f == id) {
                                // We have a child, so assume we have all
                                read = false;
                                break;
                            }
                        }
                        if (read) {
                            // AJAX Read extra hierarchy options
                            this._readHierarchy(id, next);
                        }

                        locations = [];
                        for (locationID in hierarchyLocations) {
                            location = hierarchyLocations[locationID];

                            //if (location.l == next && location.f == id) {
                            if (location.f == id) {
                                // Add the ID inside
                                location.i = locationID;
                                locations.push(location);
                            }
                        }
                    }

                    // Populate the next dropdown
                    var numLocations = locations.length,
                        selected,
                        missing,
                        option;

                    if (numLocations) {

                        // Sort location alphabetically
                        locations.sort(function(a, b) {
                            return a.n.localeCompare(b.n);
                        });

                        var dropdownSelector = selector + '_L' + next;
                        var select = $(dropdownSelector),
                            placeholder = $(dropdownSelector + ' option[value=""]').html();

                        // Remove previous options (except placeholder)
                        $(dropdownSelector + ' option').remove('[value != ""]');

                        // Populate dropdown
                        locationID = null;
                        for (i=0; i < numLocations; i++) {
                            location = locations[i];
                            locationID = location.i;
                            if (id == locationID) {
                                selected = ' selected="selected"';
                            } else {
                                selected = '';
                            }
                            if (location.l == next) {
                                // A normal level
                                missing = '';
                            } else {
                                // A link for a missing level
                                missing = ' class="missing"';
                            }
                            option = '<option value="' + locationID + '"' + selected + missing + '>' + location.n + '</option>';
                            select.append(option);
                        }

                        // Show dropdown
                        dropdown_row.removeClass('hide').show();
                        $(selector + '_L' + next + '__row1').removeClass('hide').show(); // Tuple themes

                        // Instantiate (or refresh) multiselect
                        if (select.hasClass('multiselect')) {
                            var multiSelectOptions = {
                                header: '',
                                height: 300,
                                minWidth: 0,
                                selectedList: 1,
                                noneSelectedText: placeholder,
                                multiple: false
                            };
                            if (select.hasClass('search')) {
                                select.multiselect(multiSelectOptions)
                                      .multiselectfilter({label: '', placeholder: i18n.search});
                                // Show headers
                                $('.ui-multiselect-header').show();
                            } else {
                                multiSelectOptions.header = false;
                                select.multiselect(multiSelectOptions);
                            }
                        }

                        // Auto-select single option?
                        if (numLocations == 1 && locationID) {
                            // Only 1 option so select this one
                            this._lxSelect(next, locationID, refresh);
                        }
                    }
                } else {
                    // No next level - we're at the bottom of the hierarchy
                    if (this.useGeocoder && !refresh) {
                        this._geocodeDecision();
                    }
                }
            }
            // Update the data dict
            this._collectData();

            // Zoom the map to the appropriate bounds
            this._zoomMap();
        },

        /**
         * Update the data dict from all inputs
         */
        _collectData: function() {

            var data = this.data,
                selector = '#' + this.fieldname,
                parent = this._lookupParent();

            var address = $(selector + '_address').val(),
                postcode = $(selector + '_postcode').val();

            data.address = address;
            data.postcode = postcode;

            if (data.specific) {
                // @todo: once specific = always specific? Option to revert to Lx? Use-case?
                data.id = data.specific;
                data.parent = parent;

            } else {
                var lat = data.lat,
                    lon = data.lon,
                    wkt = data.wkt;
                if (!address && !postcode && !lat && !lon && !wkt) {
                    // No specific data, so point directly to the Lowest-set Lx
                    data.id = parent;
                    data.parent = null;
                } else {
                    // We have specific data
                    data.id = null;
                    data.parent = parent;
                }
            }
            // Write data dict back to real input
            this._serialize();

            if (this.fieldname.slice(0, 4) == 'sub_') {
                // This is an S3SQLInlineComponent => trigger change event
                this.input.change();
            }
        },

        /**
         * Collect all selected Lx and write them back into the data dict
         */
        _collectLx: function() {

            var data = this.data,
                selector = '#' + this.fieldname,
                dropdown,
                level,
                value;

            for (level=0; level<6; level++) {
                dropdown = $(selector + '_L' + level);
                // Only update if the dropdown exists, else retain default
                if (dropdown.length) {
                    value = dropdown.val();
                    if (value) {
                        data['L' + level] = parseInt(value);
                    } else {
                        data['L' + level] = null;
                    }
                }
            }
            this._serialize();
        },

        /**
         * Lookup the parent of a specific location (=value of the lowest-set Lx)
         *
         * @returns {number|null} the record ID of the parent location
         */
        _lookupParent: function() {

            this._collectLx();

            var data = this.data;
                parent;
            for (var level = 5; level > -1; level--) {
                parent = data['L' + level];
                if (parent) {
                    return parent;
                }
            }
            // No Lx set at all, so return the lowest-level un-selectable Lx if-any
            var defaultLocation = hierarchyLocations['d'];
            if (defaultLocation) {
                return defaultLocation.i;
            }
            // No parent
            return null;
        },

        /**
         * Get the hierarchy labels for a country (Ajax as needed)
         *
         * @param {number} id - the location id of the country
         * @returns {object} - the labels by hierarchy level
         */
        _readLabels: function(id) {

            if (!id) {
                id = 'd';
            }

            // Read from client-side cache
            var labels = hierarchyLabels[id];
            if (labels == undefined) {

                // Get the hierarchy labels from server
                var url = S3.Ap.concat('/gis/hdata/' + id);
                $.ajaxS3({
                    async: false,
                    url: url,
                    dataType: 'script',
                    success: function(data) {
                        // Copy the elements across
                        labels = {};
                        try {
                            for (var prop in n) {
                                labels[prop] = n[prop];
                            }
                            // Store in cache
                            hierarchyLabels[id] = labels;
                            // Clear the memory
                            n = null;
                        } catch(e) {}
                    },
                    error: function(request, status, error) {
                        var msg;
                        if (error == 'UNAUTHORIZED') {
                            msg = i18n.gis_requires_login;
                        } else {
                            msg = request.responseText;
                        }
                        s3_debug(msg);
                        //S3.showAlert(msg, 'error');
                    }
                });
            }
            return labels;
        },

        /**
         * Load child location data from server to populate a dropdown
         *
         * @param {number} parent - the parent location id
         * @param {number} level - the hierarchy level (1..5)
         */
        _readHierarchy: function(parent, level) {

            var selector = '#' + this.fieldname;

            // Hide dropdown
            var dropdown = $(selector + '_L' + level),
                multiselect = false;
            dropdown.hide();
            if (dropdown.hasClass('multiselect')) {
                // Also hide MultiSelect button
                multiselect = true;
                var button = $(selector + '_L' + level + '__row button').hide();
            }

            // Show Throbber
            var throbber = $(selector + '_L' + level + '__throbber').removeClass('hide').show();

            // Download Location Data
            var url = S3.Ap.concat('/gis/ldata/' + parent);
            $.ajaxS3({
                async: false,
                url: url,
                dataType: 'script',
                success: function(data) {

                    // Copy the elements across
                    for (var prop in n) {
                        hierarchyLocations[prop] = n[prop];
                    }
                    // Clear the memory
                    n = null;

                    throbber.hide();
                    if (multiselect) {
                        button.removeClass('hide').show();
                    } else {
                        dropdown.removeClass('hide').show();
                    }
                },

                error: function(request, status, error) {
                    var msg;
                    if (error == 'UNAUTHORIZED') {
                        msg = i18n.gis_requires_login;
                    } else {
                        msg = request.responseText;
                    }
                    s3_debug(msg);
                    S3.showAlert(msg, 'error');

                    // Revert state of widget to allow user to retry
                    // without reloading page
                    throbber.hide();
                    if (multiselect) {
                        button.removeClass('hide').show();
                    } else {
                        dropdown.removeClass('hide').show();
                    }
                }
            });
        },

        /**
         * Decide whether to Geocode
         */
        _geocodeDecision: function() {

            var selector = '#' + this.fieldname,
                data = this.data;

            // Collect address and postcode
            this._collectData();

            // Address is mandatory for geocoding
            if (!data.address) {
                return;
            }

            // Lx is mandatory to the lowest level if it has options
            var levels = ['1', '2', '3', '4', '5'];
            for (var i=0, dropdown; i < 5; i++) {
                dropdown = $(selector + '_L' + levels[i]);
                if (dropdown.length && !dropdown.val()) {
                    if (dropdown[0].options.length > 1) {
                        // User hasn't yet selected an option, but can do so
                        return;
                    }
                }
            }

            // Hide previous success/failure messages
            $(selector + '_geocode .geocode_success,' +
              selector + '_geocode .geocode_fail').hide();

            var self = this,
                ns = this.namespace;
            if (this.input.data('manually_geocoded')) {
                // Show a button to allow the user to do a new automatic Geocode
                $(selector + '_geocode button').removeClass('hide')
                                               .show()
                                               .unbind(ns)
                                               .bind('click' + ns, function() {
                    $(this).hide();
                    self._geocode();
                });
            } else {
                // Do an automatic Geocode
                this._geocode();
            }
        },

        /**
         * Lookup the Lat/Lon for a Street Address
         */
        _geocode: function() {

            var fieldname = this.fieldname,
                self = this;
            var selector = '#' + fieldname;

            // Hide old messages, show throbber
            var failure = $(selector + '_geocode .geocode_fail').hide(),
                success = $(selector + '_geocode .geocode_success').hide(),
                throbber = $(selector + '_geocode .throbber').removeClass('hide').show();

            // Collect the address components
            var data = this.data,
                postData = {address: data.address},
                keys = ['postcode', 'L0', 'L1', 'L2', 'L3', 'L4', 'L5'];
            for (var i = 0, k, v; i < 7; i++) {
                k = keys[i];
                v = data[k];
                if (v) {
                    postData[k] = v;
                }
            }

            // Submit to Geocoder
            var url = S3.Ap.concat('/gis/geocode');
            $.ajaxS3({
                //async: false,
                url: url,
                type: 'POST',
                data: postData,
                dataType: 'json',
                success: function(result) {

                    var lat = result.lat,
                        lon = result.lon;

                    if (lat || lon) {
                        // Update data dict + serialize
                        data.lat = parseFloat(lat);
                        data.lon = parseFloat(lon);
                        self._serialize();

                        // If Map Showing then add/move Point
                        var gis = S3.gis;
                        if (gis.maps) {
                            var map = gis.maps['location_selector_' + fieldname];
                            if (map) {
                                var draftLayer = map.s3.draftLayer;
                                draftLayer.removeAllFeatures();
                                var geometry = new OpenLayers.Geometry.Point(data.lon, data.lat);
                                geometry.transform(gis.proj4326, map.getProjectionObject());
                                var feature = new OpenLayers.Feature.Vector(geometry);
                                draftLayer.addFeatures([feature]);
                                // Move viewport to this feature
                                self._zoomMap();
                            }
                        }

                        // Notify results
                        throbber.hide();
                        success.html(i18n.address_mapped).removeClass('hide').show();
                    } else {

                        // Notify results
                        throbber.hide();
                        failure.html(i18n.address_not_mapped).removeClass('hide').show();
                        s3_debug(result);
                    }
                },
                error: function(request, status, error) {
                    var msg;
                    if (error == 'UNAUTHORIZED') {
                        msg = i18n.gis_requires_login;
                    } else {
                        msg = request.responseText;
                    }
                    // Notify results
                    throbber.hide();
                    failure.html(i18n.address_not_mapped).removeClass('hide').show();
                    s3_debug(msg);
                }
            });
        },

        /**
         * Lookup the Location of a Lat/Lon
         */
        _geocodeReverse: function() {

            var fieldname = this.fieldname,
                self = this;
            var selector = '#' + fieldname;

            // Hide old messages, show throbber
            var failure = $(selector + '_geocode .geocode_fail').hide(),
                success = $(selector + '_geocode .geocode_success').hide(),
                throbber = $(selector + '_geocode .throbber').removeClass('hide').show();

            // Collect the Lat/Lon
            var data = this.data;
            var postData = {lat: data.lat, lon: data.lon};

            // Submit to Geocoder
            var url = S3.Ap.concat('/gis/geocode_r');
            $.ajaxS3({
                async: false,
                url: url,
                type: 'POST',
                data: postData,
                dataType: 'json',
                success: function(result) {
                    if (result.L0) {
                        // Prevent forward geocoding
                        self.useGeocoder = false;
                        self._lxSelect(0, result.L0);
                        if (result.L1) {
                            self._lxSelect(1, result.L1);
                        }
                        if (result.L2) {
                            self._lxSelect(2, result.L2);
                        }
                        if (result.L3) {
                            self._lxSelect(3, result.L3);
                        }
                        if (result.L4) {
                            self._lxSelect(4, result.L4);
                        }
                        if (result.L5) {
                            self._lxSelect(5, result.L5);
                        }
                        // Reset Geocoder-option
                        self.useGeocoder = true;
                        // Notify results
                        throbber.hide();
                        success.html(i18n.location_found).removeClass('hide').show();
                    } else {
                        // Notify results
                        throbber.hide();
                        failure.html(i18n.location_not_found).removeClass('hide').show();
                        //s3_debug(result);
                    }
                },
                error: function(request, status, error) {
                    var msg;
                    if (error == 'UNAUTHORIZED') {
                        msg = i18n.gis_requires_login;
                    } else {
                        msg = request.responseText;
                    }
                    // Notify results
                    throbber.hide();
                    failure.html(i18n.location_not_found).removeClass('hide').show();
                    s3_debug(msg);
                }
            });
        },

        /**
         * Show the Map
         * - this doesn't imply that a specific location is to be created
         * - that only happens if a Point is created on the Map
         *
         * @param {event} event - the event if called from an event handler
         */
        _showMap: function(event) {

            var fieldname = this.fieldname,
                ns = this.namespace,
                self = this;

            var selector = '#' + fieldname;

            // Change click-event and label of map icon
            $(selector + '_map_icon').unbind(ns)
                                     .bind('click' + ns, function() {
                self._hideMap();
            });
            $(selector + '_map_icon span').html(i18n.hide_map);

            // Show the Map
            var map_wrapper = $(selector + '_map_wrapper').hide()
                                                          .removeClass('hide')
                                                          .slideDown('medium');
            if (map_wrapper.length && event) {
                // Scroll to this section
                $('html,body').animate({scrollTop: map_wrapper.offset().top}, 250);
            }

            var realInput = this.input,
                data = this.data;

            // Check if Maps JS is Loaded
            $.when(this._jsLoaded()).then(

                function(status) {
                    // Maps JS is loaded
                    var gis = S3.gis,
                        map_id = 'location_selector_' + fieldname;

                    if (!gis.maps[map_id]) {

                        // Instantiate the Map as we couldn't do it when DIV is hidden
                        var map = gis.show_map(map_id);

                        // Zoom to the appropriate bounds
                        self._zoomMap();

                        // Display the feature (if any)
                        var lat = data.lat,
                            lon = data.lon,
                            wkt = data.wkt,
                            feature,
                            geometry;
                        if (lat || lon || wkt) {
                            if ((wkt != undefined) && wkt) {
                                var in_options = {'internalProjection': map.getProjectionObject(),
                                                  'externalProjection': gis.proj4326
                                                  };
                                feature = new OpenLayers.Format.WKT(in_options).read(wkt);
                            } else {
                                geometry = new OpenLayers.Geometry.Point(parseFloat(lon), parseFloat(lat));
                                geometry.transform(gis.proj4326, map.getProjectionObject());
                                feature = new OpenLayers.Feature.Vector(geometry);
                            }
                            map.s3.draftLayer.addFeatures([feature]);
                        }

                        // Does the map have controls to add new features?
                        var controls = map.controls,
                            control;
                        for (var i=0, len=controls.length; i < len; i++) {
                            if (controls[i].CLASS_NAME == 'OpenLayers.Control.DrawFeature') {
                                control = controls[i];
                                break;
                            }
                        }
                        if (control) {
                            // Watch for new features being selected, so that we can
                            // store the Lat/Lon/WKT (callback function for the map)
                            // @todo: make this callback specific for this map
                            map.s3.pointPlaced = function(feature) {

                                // Hide any Geocoder messages
                                $(selector + '_geocode .geocode_fail').hide();
                                $(selector + '_geocode .geocode_success').hide();

                                // Update the Form fields
                                var geometry = feature.geometry;

                                if (geometry.CLASS_NAME == 'OpenLayers.Geometry.Point') {
                                    var centerPoint = geometry.getBounds().getCenterLonLat();
                                    centerPoint.transform(map.getProjectionObject(), gis.proj4326);

                                    // Store the data
                                    data.wkt = null;
                                    data.lat = centerPoint.lat;
                                    data.lon = centerPoint.lon;

                                    // Reverse Geocode the Point
                                    if (!data.address && this.useGeocoder) {
                                        self._geocodeReverse();
                                    }
                                } else {
                                    // Polygon
                                    var out_options = {
                                        'internalProjection': map.getProjectionObject(),
                                        'externalProjection': gis.proj4326
                                        };
                                    wkt = new OpenLayers.Format.WKT(out_options).write(feature);

                                    // Store the data
                                    data.wkt = wkt;
                                    data.lat = null;
                                    data.lon = null;
                                }
                                // Store the fact that we've now added Marker manually
                                realInput.data('manually_geocoded', true);
                                // Serialize the data dict
                                self._collectData();
                                // Remove all errors
                                self._removeErrors();
                            };
                            //control.events.register('featureadded', null, pointPlaced);
                        }
                    } else {
                        // Map already instantiated (@todo: remove this section?)
                        //var map = gis.maps[map_id];
                    }
                },
                function(status) {
                    // Failed
                    s3_debug(status);
                },
                function(status) {
                    // Progress
                    s3_debug(status);
                }
            );
        },

        /**
         * Hide the Map
         * - this also acts as a 'Cancel' for the addition of Lat/Lon/WKT fields
         */
        _hideMap: function() {

            var fieldname = this.fieldname,
                ns = this.namespace;

            var selector = '#' + fieldname;

            // Update the click-event handler of the map icon
            var self = this;
            $(selector + '_map_icon').unbind(ns)
                                     .bind('click' + ns, function(e) {
                self._showMap(e);
            });

            // Hide the Map
            $(selector + '_map_wrapper').slideUp('medium');

            var data = this.data,
                iconLabel;
            if (data.specific) {
                iconLabel = i18n.show_map_view;
            } else {
                iconLabel = i18n.show_map_add;
                if (S3.gis.maps) {
                    var map = S3.gis.maps['location_selector_' + fieldname];
                    if (map) {
                        // Remove the Feature (if-any)
                        map.s3.draftLayer.removeAllFeatures();

                        // Reset Lat/Lon/WKT
                        data.lat = null;
                        data.lon = null;
                        data.wkt = null;

                        this.input.data('manually_geocoded', false);

                        // Write back to real input
                        this._collectData();
                    }
                }
            }
            // Change the label of the map icon
            $(selector + '_map_icon span').html(iconLabel);
        },

        /**
         * Zoom the Map to appropriate bounds
         *
         * @param {number} id - the record ID of the Lx location to zoom to
         *                      (will be ignored if we have lat/lon set)
         */
        _zoomMap: function(id) {

            var fieldname = this.fieldname;

            var gis = S3.gis;
            if (gis.maps) {

                var map = gis.maps['location_selector_' + fieldname];
                if (map) {

                    // Zoom to point, if we have it
                    var data = this.data;
                    var lat = data.lat,
                        lon = data.lon,
                        wkt = data.wkt,
                        bounds;

                    if (lat && lon) {
                        // Minimal bbox and padding will be added inside S3.gis.zoomBounds
                        bounds = [lon, lat, lon, lat];
                    } else if (wkt) {
                        // Experimental
                        var vector = new OpenLayers.Feature.Vector(OpenLayers.Geometry.fromWKT(wkt));
                        S3.gis.zoomBounds(map, vector.geometry.getBounds());
                    } else {
                        // Zoom to extent of the Lx, if we have it
                        if (!id) {
                            // Use default bounds if lookupParent fails
                            id = this._lookupParent() || 'd';
                        }
                        bounds = hierarchyLocations[id].b;
                        if (!bounds || !bounds.length) {
                            // Try parent locations
                            var parent = hierarchyLocations[id].f,
                                parentLocation,
                                maxLevels = 4;
                            while(parent && maxLevels) {
                                maxLevels--;
                                parentLocation = hierarchyLocations[parent];
                                bounds = parentLocation.b;
                                if (bounds || parentLocation.l === 0) {
                                    break;
                                } else {
                                    parent = parentLocation.f;
                                }
                            }
                        }
                    }
                    if (bounds) {
                        bounds = OpenLayers.Bounds.fromArray(bounds);
                        S3.gis.zoomBounds(map, bounds);
                    }
                }
            }
        },

        /**
         * Client-side validation of the widget before main-form submission
         * - checks for required fields
         *
         * @returns {bool} - whether widget input is valid or not
         *
         * @todo: skip if widget is invisible
         * @todo: needs a different trigger in inline-forms (see _bindEvents)
         */
        _submitForm: function() {

            var fieldname = this.fieldname;

            // Remove previous errors
            this._removeErrors();

            // Do we have a value to submit?
            var selector = '#' + fieldname,
                current_value = this.data.id,
                suffix = ['address', 'L5', 'L4', 'L3', 'L2', 'L1', 'L0'],
                i,
                s,
                f;

            if (current_value) {
                if (!hierarchyLocations[current_value]) {
                    // Specific location => ok
                    return true;
                }
                var current_level = hierarchyLocations[current_value].l;
                // Is a higher-level required? If so, then prevent submission
                for (i = 0; i < 6 - current_level; i++) {
                    s = selector + '_' + suffix[i];
                    f = $(s);
                    if (f.length && f.hasClass('required') && f.is(':visible')) {
                        S3.fieldError(s, i18n.enter_value);
                        return false;
                    }
                }
                return true;
            } else {
                var data = this.data;
                if (data.lat || data.lon || data.wkt || data.address || data.postcode) {
                    // Specific location => ok
                    return true;
                }
                // Is any level required? If so, then prevent submission
                for (i = 0; i < 7; i++) {
                    s = selector + '_' + suffix[i];
                    f = $(s);
                    if (f.length && f.hasClass('required') && f.is(':visible')) {
                        S3.fieldError(s, i18n.enter_value);
                        return false;
                    }
                }
                return true;
            }
        },

        /**
         * Encode this.data as JSON and write into real input
         *
         * @returns {JSON} the JSON data
         */
        _serialize: function() {

            var json = JSON.stringify(this.data);
            this.input.val(json);

            return json;
        },

        /**
         * Parse the JSON from real input into this.data
         *
         * @returns {object} this.data
         */
        _deserialize: function() {

            var value = this.input.val();
            this.data = JSON.parse(value);

            return this.data;
        },

        /**
         * Store hierarchy data in the global cache
         *
         * @param {object} labels: the hierarchy labels
         * @param {object} locations: the location data
         */
        _storeHierarchyData: function(labels, locations) {

            var locationID;
            if (locations) {
                for (locationID in locations) {
                    hierarchyLocations[locationID] = locations[locationID];
                }
            }
            if (labels) {
                for (locationID in labels) {
                    hierarchyLabels[locationID] = labels[locationID];
                }
            }
        },

        /**
         * Check that Map JS is Loaded
         * - used if a tab containing a Map is unhidden
         */
        _jsLoaded: function() {

            var dfd = new jQuery.Deferred();

            // Test every half-second
            setTimeout(function working() {
                if (S3.gis.maps != undefined) {
                    dfd.resolve('loaded');
                } else if (dfd.state() === 'pending') {
                    // Notify progress
                    dfd.notify('waiting for JS to load...');
                    // Loop
                    setTimeout(working, 500);
                } else {
                    // Failed!?
                }
            }, 1);
            // Return the Promise so caller can't change the Deferred
            return dfd.promise();
        },

        /**
         * Remove error messages
         *
         * @param {jQuery} element - the input field (removes all error messages
         *                           in the widget if no field specified)
         */
        _removeErrors: function(element) {

            if (!element) {
                var selector = '#' + this.fieldname;
                element = selector + '_L0,' +
                          selector + '_L1,' +
                          selector + '_L2,' +
                          selector + '_L3,' +
                          selector + '_L4,' +
                          selector + '_L5,' +
                          selector + '_address,' +
                          selector + '_postcode';
            }
            $(element).siblings('.error').remove();
        },

        /**
         * Bind event handlers (after refresh)
         */
        _bindEvents: function() {

            var selector = '#' + this.fieldname,
                ns = this.namespace,
                self = this;

            $(selector + '_L0').bind('change' + ns, function() {
                self._removeErrors(this);
                self._lxSelect(0);
            });
            $(selector + '_L1').bind('change' + ns, function() {
                self._removeErrors(this);
                self._lxSelect(1);
            });
            $(selector + '_L2').bind('change' + ns, function() {
                self._removeErrors(this);
                self._lxSelect(2);
            });
            $(selector + '_L3').bind('change' + ns, function() {
                self._removeErrors(this);
                self._lxSelect(3);
            });
            $(selector + '_L4').bind('change' + ns, function() {
                self._removeErrors(this);
                self._lxSelect(4);
            });
            $(selector + '_L5').bind('change' + ns, function() {
                self._removeErrors(this);
                self._lxSelect(5);
            });

            $(selector + '_address,' +
              selector + '_postcode').bind('change' + ns, function() {
                self._removeErrors(this);
                if (this.useGeocoder) {
                    // geocodeDecision includes collectData
                    //self._collectData();
                    self._geocodeDecision();
                } else {
                    self._collectData();
                }
            });

            // @todo: must use a different trigger in inline-forms
            this.input.closest('form').bind('submit' + ns + this.id, function(e) {
                e.preventDefault();
                if (self._submitForm()) {
                    self.input.closest('form').unbind(ns + self.id).submit();
                }
            });
            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var selector = '#' + this.fieldname,
                ns = this.namespace;

            $(selector + '_L0,' +
              selector + '_L1,' +
              selector + '_L2,' +
              selector + '_L3,' +
              selector + '_L4,' +
              selector + '_L5,' +
              selector + '_address,' +
              selector + '_postcode,' +
              selector + '_map_icon').unbind(ns);

            this.input.next('.error_wrapper').unbind(ns);
            this.input.closest('form').unbind(ns + self.id);

            return true;
        }
    });
})(jQuery);
