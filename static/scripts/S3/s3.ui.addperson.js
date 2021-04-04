/**
 * jQuery UI Widget for S3AddPersonWidget
 *
 * @copyright 2017-2021 (c) Sahana Software Foundation
 * @license MIT
 *
 * requires jQuery 1.9.1+
 * requires jQuery UI 1.10 widget factory
 */

(function($, undefined) {

    "use strict";

    // ========================================================================
    /**
     * Universal URL Query Updater
     *
     * @param {string} url - the URL to update
     * @param {object} queries - object describing the queries to update
     *
     * @returns {string} - the updated URL
     *
     * @example
     *  var url = "http://host/path?first=one&second=two#hash";
     *  updateURLQuery(url, {
     *      'first': 'updated',  // update
     *      'second': null,      // remove
     *      'third': 'new'       // add
     *  });
     *  // => 'http://host/path?first=updated&third=new#hash'
     *
     * @todo: consider moving into S3
     */
    var updateURLQuery = function(url, queries) {

        var encode = function(key, value) {
            if (value) {
                return encodeURIComponent(key) + '=' + encodeURIComponent(value);
            } else {
                return '';
            }
        };

        var urlParts = url.split('?'),
            postQuestion = urlParts[1] || '';
        urlParts = [urlParts[0]].concat(postQuestion.split('#'));

        var query = urlParts[1],
            key,
            getVars,
            replaced = {},
            q;

        if (query) {
            getVars = query.split('&').map(function(param) {
                key = decodeURIComponent(param.split('=')[0]);
                if (queries.hasOwnProperty(key)) {
                    replaced[key] = true;
                    return encode(key, queries[key]);
                } else {
                    return param;
                }
            }).filter(function(p) { return p; });
        } else {
            getVars = [];
        }

        for (key in queries) {
            if (!replaced[key]) {
                q = encode(key, queries[key]);
                if (q) {
                    getVars.push(q);
                }
            }
        }

        var newUrl = urlParts[0];
        if (getVars.length) {
            newUrl += '?' + getVars.join('&');
        }
        if (urlParts[2]) {
            newUrl += '#' + urlParts[2];
        }
        return newUrl;
    };

    // ========================================================================
    /**
     * A promise that resolves when addPersonWidget is ready, allows earlier
     * functions to attach callbacks (e.g. lookupContact)
     *
     * @param {string} fieldID - the ID of the person_id input
     *
     * @returns {promise} - a promise that gets resolved when the widget
     *                      is loaded and ready
     *
     * @example
     *  $.when(S3.addPersonWidgetReady(fieldname))
     *   .then(function(widget) {
     *      widget.addPerson('lookupContact', siteID);
     *  });
     */
    S3.addPersonWidgetReady = function(fieldID) {

        var deferred = new jQuery.Deferred(),
            input = $('#' + fieldID);

        if (input.data('lookup_contact') !== undefined) {
            // Already loaded
            deferred.resolve(input);
        } else {
            // Wait for addPersonReady event
            input.on('addPersonReady', function() {
                deferred.resolve(input);
            });
        }
        return deferred.promise();
    };

    // ========================================================================

    var addPersonID = 0;

    /**
     * addPerson UI Widget
     */
    $.widget('s3.addPerson', {

        // --------------------------------------------------------------------
        /**
         * Default options
         *
         * @property {bool} lookupDuplicates - activate duplicates checking
         * @property {bool} separateNameFields - use separate fields for
         *                                       first/middle/last name parts
         *
         * @property {string} trigger - name of the autocomplete trigger field
         * @property {string} c - the autocomplete controller
         * @property {string} f - the autocomplete function
         * @property {string} tags - a list of Tag fields
         * @property {number} chars - the minimum number of characters that
         *                            must be entered to trigger the autocomplete
         * @property {number} delay - the delay (in milliseconds) before the
         *                            autocomplete is triggered
         *
         * @property {string} downIcon - CSS class for the icon to open the
         *                               duplicate search result list
         * @property {string} yesIcon - CSS class for the icon to confirm a
         *                              duplicate
         * @property {string} noIcon - CSS class for the icon to decline all
         *                             duplicates
         */
        options: {

            lookupDuplicates: false,
            separateNameFields: false,
            trigger: 'full_name',

            c: 'pr',
            f: 'person',

            tags: [],

            chars: 2,
            delay: 800,

            downIcon: 'fa fa-caret-down',
            yesIcon: 'fa fa-check',
            noIcon: 'fa fa-remove'
        },

        // --------------------------------------------------------------------
        /**
         * Create the widget
         */
        _create: function() {

            //var el = $(this.element);

            this.id = addPersonID;
            addPersonID += 1;

            this.eventNamespace = '.addPerson';
        },

        // --------------------------------------------------------------------
        /**
         * Update the widget options
         */
        _init: function() {

            var el = $(this.element),
                opts = this.options,
                fieldName = el.attr('id');

            this.fieldName = fieldName;
            this.selector = '#' + fieldName;

            this.data = {};

            // Determine form style
            var realRow = $(this.selector + '__row').hide();
            if (realRow.hasClass('form-row') || realRow.hasClass('control-group')) {
                // Foundation or Bootstrap form style
                this.formStyle = 'div';
            } else {
                // Legacy table form style
                this.formStyle = 'table';
            }

            // Fields at the top
            this.topFields = [
                'organisation_id',
                'pe_label'
            ];

            // ID Label field
            var idLabel = $(this.selector + '_pe_label');
            if (idLabel.length) {
                this.idLabel = idLabel;
            }

            // Name fields (in order of appearance) and AC trigger
            var triggerName = opts.trigger,
                nameFields;
            if (opts.separateNameFields) {
                if (triggerName == 'first_name') {
                    nameFields = ['first_name', 'middle_name', 'last_name'];
                } else {
                    triggerName = 'last_name';
                    nameFields = ['last_name', 'middle_name', 'first_name'];
                }
            } else {
                triggerName = 'full_name';
                nameFields = ['full_name'];
            }
            opts.trigger = triggerName;
            this.triggerRow = $(this._rowSelector(triggerName));
            this.trigger = $(this.selector + '_' + triggerName);
            this.nameFields = nameFields;

            // All other fields (in order of appearance)
            var personFields = [
                'father_name',
                'grandfather_name',
                'year_of_birth',
                'date_of_birth',
                'gender',
                'occupation',
                'mobile_phone',
                'home_phone',
                'email'
            ];
            opts.tags.forEach(function(tag) {
                if (personFields.indexOf(tag) == -1) {
                    personFields.push(tag);
                }
            });
            this.personFields = personFields;

            this._arrangeFormRows();

            this.refresh();
        },

        // --------------------------------------------------------------------
        /**
         * Remove generated elements & reset other changes
         */
        _destroy: function() {

            $.Widget.prototype.destroy.call(this);
        },

        // --------------------------------------------------------------------
        /**
         * Redraw contents
         */
        refresh: function() {

            var el = $(this.element),
                selector = this.selector,
                opts = this.options;

            this._unbindEvents();
            this.pendingAC = false;

            // Autocomplete throbber
            var throbber = this.throbber;
            if (throbber) {
                throbber.remove();
            }
            throbber = $('<div class="throbber input_throbber"></div>');
            throbber.hide().insertAfter(this.trigger);
            this.throbber = throbber;

            // ID Label Lookup Throbber
            var idLabel = this.idLabel;
            if (idLabel) {
                throbber = $('<div class="throbber input_throbber"></div>');
                throbber.hide().insertAfter(idLabel);
                this.idLabelThrobber = throbber;
            }

            var value = el.val();
            if (value) {
                if (!isNaN(value - 0)) {
                    // Ensure main input has proper JSON
                    this.data = {'id': value};
                    this._serialize();
                }
                if (this.data.id) {
                    // Disable input if we have a valid ID
                    this._disableInputs();
                    this._toggleActions({cancel: false});
                } else {
                    // We have some input data, but no ID
                    // => probably a validation error, so leave editable
                    this._enableAutocomplete();
                    this._toggleActions({edit: false});
                }
            } else {
                this._serialize();
                this._enableAutocomplete();
                this._toggleActions({edit: false});
            }

            // Show the edit bar
            $(selector + '_edit_bar').removeClass('hide').show();

            if (opts.lookupDuplicates) {

                var resultsID = this.fieldName + '_duplicates';
                if (!$('#' + resultsID).length) {
                    // Add place to store results
                    // @todo: replace class "req" with widget-specific class
                    var results = '<div id="' + resultsID + '" class="req"></div>';
                    if (this.formStyle == 'div') {
                        $(selector + '_box_bottom').before(results);
                    } else {
                        $(selector + '_box_bottom1').before(results);
                    }
                }
            }

            this._bindEvents();

            el.trigger('addPersonReady');
        },

        // --------------------------------------------------------------------
        /**
         * Arrange the embedded form rows
         */
        _arrangeFormRows: function() {

            var el = $(this.element),
                //fieldName = this.fieldName,
                selector = this.selector,
                realRow = $(selector + '__row').hide(),
                formStyle = this.formStyle;

            if (formStyle == 'div') {
                // Insert the bottom box
                $(selector + '_box_bottom').removeClass('hide')
                                           .show()
                                           .insertAfter(realRow);

                // Insert all embedded form rows after the real row
                var self = this,
                    allFields = this.topFields.concat(this.nameFields)
                                              .concat(this.personFields)
                                              .reverse();

                allFields.forEach(function(fieldName) {
                    realRow.after($(self._rowSelector(fieldName)));
                });

                // Unhide the embedded form rows
                $(allFields.map(this._rowSelector, this).join(',')).removeClass('hide').show();

            } else {
                // Hide the main row
                $(selector + '__row1').hide();
            }

            // Insert title row and error wrapper
            var titleRow = $(selector + '_title__row'),
                errorWrapper = el.next('.error_wrapper');
            realRow.after(errorWrapper)
                   .after(titleRow.removeClass('hide').show());
        },

        // --------------------------------------------------------------------
        /**
         * Get all field names
         *
         * @returns {Array} - an Array with all field names, in order
         *                    of appearance in the form
         */
        _allFields: function() {

            return this.topFields.concat(this.nameFields)
                                 .concat(this.personFields);
        },

        // --------------------------------------------------------------------
        /**
         * Map field name <=> JSON object property, for encoding/decoding
         * server-side JSON data
         *
         * @returns {object} - a field map {fieldName: jsonPropertyName}
         */
        _fieldMap: function() {

            var map = {
                'pe_label': 'pe_label',
                'email': 'email',
                'mobile_phone': 'mphone',
                'home_phone': 'hphone',
                'gender': 'sex',
                'date_of_birth': 'dob',
                'year_of_birth': 'year_of_birth',
                'father_name': 'father_name',
                'grandfather_name': 'grandfather_name',
                'occupation': 'occupation',
                'organisation_id': 'org_id'
            };
            if (this.options.separateNameFields) {
                map.first_name = 'first_name';
                map.middle_name = 'middle_name';
                map.last_name = 'last_name';
            }
            this.options.tags.forEach(function(tag) {
                if (!map.hasOwnProperty(tag)) {
                    map[tag] = tag;
                }
            });

            return map;
        },

        // --------------------------------------------------------------------
        /**
         * Get a CSS selector for the form row containing a certain field
         *
         * @param {string} fieldName - the field name
         *
         * @returns {string} - the CSS selector for the form row containing
         *                     the field
         */
        _rowSelector: function(fieldName) {

            return this.selector + '_' + fieldName + '__row';
        },

        // --------------------------------------------------------------------
        /**
         * Read values from inputs and write them into this.data
         */
        _readInputs: function() {

            var selector = this.selector,
                data = {},
                field;

            this._allFields().forEach(function(fieldName) {
                field = $(selector + '_' + fieldName);
                if (field.length) {
                    data[fieldName] = field.val();
                }
            });
            this.data = data;
        },

        // --------------------------------------------------------------------
        /**
         * Update inputs from this.data
         */
        _updateInputs: function() {

            var selector = this.selector,
                data = this.data,
                field;

            this._allFields().forEach(function(fieldName) {
                field = $(selector + '_' + fieldName);
                if (field.length && data.hasOwnProperty(fieldName)) {
                    field.val(data[fieldName]);
                }
            });
        },

        // --------------------------------------------------------------------
        /**
         * Convert this.data to JSON and write into main input
         */
        _serialize: function() {

            $(this.element).val(JSON.stringify(this.data));
        },

        // --------------------------------------------------------------------
        /**
         * Parse main input value and write to this.data
         */
        _deserialize: function() {

            var value = $(this.element).val(),
                personID = value - 0,
                data;

            if (isNaN(personID)) {
                data = JSON.parse(value);
            } else {
                data = {'id': personID};
            }
            this.data = data;
        },

        // --------------------------------------------------------------------
        /**
         * Toggle visibility of edit bar actions (=edit, cancel)
         *
         * @param {object} visibility - object with visibility flags:
         *                              {action: true|false}
         */
        _toggleActions: function(visibility) {

            var selectors = {
                    edit: '.edit-action',
                    cancel: '.cancel-action'
                },
                selector = this.selector,
                action,
                actionItem;

            for (action in visibility) {
                actionItem = $(selector + '_edit_bar ' + selectors[action]);
                if (visibility[action]) {
                    actionItem.removeClass('hide').show();
                } else {
                    actionItem.hide();
                }
            }
        },

        // --------------------------------------------------------------------
        /**
         * Toggle visibility of the DoB calendar widget triggers
         *
         * @param {Boolean} visibility - true to show, false to hide
         */
        _toggleDatePickerTrigger: function(visibility) {

            var clearBtn = $(this.selector + '_date_of_birth__row .calendar-clear-btn'),
                trigger = $(this.selector + '_date_of_birth__row .ui-datepicker-trigger');
            if (visibility) {
                trigger.removeClass('hide').show();
                clearBtn.removeClass('hide').show();
            } else {
                trigger.hide();
                clearBtn.hide();
            }
        },

        // --------------------------------------------------------------------
        /**
         * Enable all input fields
         */
        _enableInputs: function() {

            var selector = this.selector,
                allFields = this._allFields();

            allFields.forEach(function(fieldName) {
                $(selector + '_' + fieldName).prop('disabled', false);
            });

            this._toggleDatePickerTrigger(true);
        },

        // --------------------------------------------------------------------
        /**
         * Disable all input fields
         */
        _disableInputs: function() {

            var selector = this.selector,
                allFields = this._allFields();

            allFields.forEach(function(fieldName) {
                $(selector + '_' + fieldName).prop('disabled', true);
            });

            this._toggleDatePickerTrigger(false);

            this._toggleActions({edit: true, cancel: false});
        },

        // --------------------------------------------------------------------
        /**
         * Reset this.data, clear and enable all input fields
         *
         * @param {Bool} keepNames - keep the values in name fields
         */
        _reset: function(keepNames) {

            // Get the field names
            var fieldNames = this.topFields.concat(this.personFields);
            if (!keepNames) {
                fieldNames = fieldNames.concat(this.nameFields);
            }

            // Clear and enable the fields
            var selector = this.selector;
            fieldNames.forEach(function(fieldName) {
                $(selector + '_' + fieldName).prop('disabled', false).val('');
            });

            // Enable date picker triggers
            this._toggleDatePickerTrigger(true);

            // Remove data and serialize
            if (keepNames) {
                this._readInputs();
            } else {
                this.data = {};
            }
            this._serialize();
        },

        // --------------------------------------------------------------------
        /**
         * Edit the current selection, or actually: cancel the selection and
         * start selecting/entering a different person
         */
        _edit: function() {

            // Store previous selection so it can be reverted to
            this.previousSelection = $.extend({}, this.data);

            this._reset();

            this._enableAutocomplete();
            this._toggleActions({edit: false, cancel: true});
        },

        // --------------------------------------------------------------------
        /**
         * Cancel entering a new person, and revert to previous selection
         */
        _cancel: function() {

            var previous = this.previousSelection;

            // Cancel pending AC
            if (this.pendingAC) {
                this.pendingAC.abort();
                this.pendingAC = false;
                this.throbber.hide();
            }

            if (previous && Object.values(previous).length) {

                this.data = $.extend({}, this.previousSelection);
                this._serialize();

                this._updateInputs();
                this._disableInputs();

            } else {

                // No previous selection, just reset
                this._reset();
            }

            this._clearDuplicates();
        },

        // --------------------------------------------------------------------
        /**
         * Remove error messages (click-handler for error-wrapper)
         */
        _clearError: function() {

            $(this.selector + '_title__row').next('.error_wrapper')
                                            .fadeOut('slow', function() {
                                                S3.hideAlerts();
                                            });
        },

        // --------------------------------------------------------------------
        /**
         * Get the name of an Autocomplete-item
         * => to fill the name input after selection
         *
         * @param {object} item - the autocomplete item
         *
         * @returns {string} - the name
         */
        _fullName: function(item) {

            if (item.label !== undefined) {
                // No Match
                return item.label;
            }
            return item.name;
        },

        // --------------------------------------------------------------------
        /**
         * Get a label for an Autocomplete-item
         * => for the drop-down
         *
         * @param {object} item - the item
         *
         * @returns {string} - the label
         */
        _autocompleteLabel: function(item) {

            if (item.label !== undefined) {
                // No Match
                return item.label;
            }

            var label = item.name,
                details = [
                    item.job,
                    item.org
                ].filter(function(s) { return s; });

            if (details.length) {
                label += ' (' + details.join(',') + ')';
            }
            if (this.idLabel) {
                var pe_label = item.pe_label;
                if (pe_label) {
                    label += ' <span class="pe-label">[' + pe_label + ']</span> ';
                }
            }
            return label;
        },

        // --------------------------------------------------------------------
        /**
         * Enable the Autocomplete on the trigger field
         */
        _enableAutocomplete: function() {

            var trigger = this.trigger;
            if (trigger.attr('autocomplete')) {
                // Already set up
                return;
            }

            var opts = this.options,
                self = this;

            this.acURL = S3.Ap.concat('/' + opts.c + '/' + opts.f + '/search_ac');
            if (this.idLabel) {
                this.acURL += '?label=1';
            }

            // Instantiate AC
            var acInstance = trigger.autocomplete({

                delay: opts.delay,
                minLength: opts.chars,

                source: function(request, response) {
                    // Patch the source so that we can handle "None of the above"
                    if (self.pendingAC) {
                        self.pendingAC.abort();
                    }
                    self.pendingAC = $.ajax({
                        url: self.acURL,
                        data: {
                            term: request.term
                        }
                    }).done(function (data) {
                        if (data.length === 0) {
                            // No match => new entry
                            delete self.data.id;
                        } else {
                            // Append "None of the above" to list of matches
                            data.push({
                                id: 0,
                                value: '',
                                label: i18n.none_of_the_above
                            });
                        }
                        response(data);
                    });
                },

                search: function(/* event, ui */) {
                    self.throbber.show();
                    return true;
                },

                response: function(event, ui, content) {
                    self.throbber.hide();
                    return content;
                },

                focus: function(/* event, ui */) {
                    return false;
                },

                select: function(event, ui) {
                    var item = ui.item;
                    if (item.id) {
                        if (!opts.separateNameFields) {
                            trigger.val(self._fullName(item));
                        }
                        self._selectPerson(item.id);
                    } else {
                        // 'None of the above' => New Entry
                        delete self.data.id;
                    }
                    return false;
                }
            }).data('ui-autocomplete');

            if (acInstance) {
                // Override standard drop-down item renderer
                acInstance._renderItem = function(ul, item) {
                    var label = self._autocompleteLabel(item);
                    return $('<li>').data('item.autocomplete', item)
                                    .append('<a>' + label + '</a>')
                                    .appendTo(ul);
                };
            }
        },

        // --------------------------------------------------------------------
        /**
         * Select a person from a list of alternatives; performs an Ajax lookup
         * of the person details for the selected item and populates the input
         * fields
         *
         * @param {integer} itemID - the selected item ID
         */
        _selectPerson: function(itemID) {

            var opts = this.options;

            // Enable all name fields, clear all names except trigger
            var selector = this.selector,
                triggerName = opts.trigger,
                field;
            this.nameFields.forEach(function(fieldName) {
                field = $(selector + '_' + fieldName).prop('disabled', false);
                if (fieldName != triggerName) {
                    field.val('');
                }
            });

            // Clear+enable all other input fields
            this._reset(true);

            var self = this,
                trigger = this.trigger,
                url = S3.Ap.concat('/' + opts.c + '/' + opts.f + '/' + itemID + '/lookup.json');

            if (this.idLabel) {
                url += '?label=1';
            }

            // Show throbber during the Ajax lookup
            this.throbber.show();
            if (!trigger.val()) {
                trigger.attr('placeholder', i18n.loading + '...');
            }

            // Ajax lookup
            $.getJSONS3(url, function(data) {
                try {
                    self.data.id = itemID;
                    if (!opts.separateNameFields) {
                        self.data.full_name = trigger.val();
                    }
                    self._processReponse(data);
                } catch(e) {
                    self._reset(true);
                }
                self.throbber.hide();
                trigger.removeAttr('placeholder');
            });
        },

        // --------------------------------------------------------------------
        /**
         * Process the response from pr_person_lookup, hrm_lookup or
         * site_contact_person
         *
         * @param {object} data - the JSON object with the server data
         */
        _processReponse: function(data) {

            var fieldMap = this._fieldMap();

            // Fill the input fields, and store as previous selection
            var current = this.data,
                fieldName,
                propertyName;

            for (fieldName in fieldMap) {
                propertyName = fieldMap[fieldName] || fieldName;
                if (data.hasOwnProperty(propertyName)) {
                    current[fieldName] = data[propertyName];
                }
            }
            this._serialize();

            // Store as previous selection so it can be reverted to
            this.previousSelection = $.extend({}, this.data);

            this._updateInputs();
            this._disableInputs();
        },

        // --------------------------------------------------------------------
        /**
         * Look up a person from the ID Label (pe_label)
         */
        lookupIDLabel: function() {

            var idLabel = this.idLabel;
            if (!idLabel) {
                return;
            }

            var value = idLabel.val();
            if (!value) {
                // @todo: require minimum length?
                return;
            }

            // Cancel any previous lookup
            var lookup = idLabel.data('lookup');
            if (lookup) {
                lookup.abort();
                idLabel.data('lookup', null);
            }

            var opts = this.options,
                getName = "";
            if (!opts.separateNameFields) {
                getName = "&name=1";
            }

            var self = this,
                throbber = this.idLabelThrobber.show(),
                url = S3.Ap.concat('/' + opts.c + '/' + opts.f + '/lookup.json?search=1&label=1' + getName + '&~.pe_label=' + value);

            // Ajax lookup
            lookup = $.getJSONS3(url, function(data) {
                if (data.pe_label) {
                    self.data.id = data.id;
                    if (!opts.separateNameFields) {
                        self.data.full_name = data.name;
                    }
                    self._processReponse(data);
                }
                idLabel.data('lookup', null);
                throbber.hide();
            });
            idLabel.data('lookup', lookup);
        },

        // --------------------------------------------------------------------
        /**
         * Public method to populate the widget with the contact person
         * of a site
         *
         * @param {integer} siteID - the site ID
         */
        lookupContact: function(siteID) {

            // Clear+enable all input fields
            this._reset();

            var opts = this.options,
                trigger = this.trigger,
                self = this,
                url = S3.Ap.concat('/org/site/' + siteID + '/site_contact_person');

            // Show throbber during the Ajax lookup
            this.throbber.show();
            if (!trigger.val()) {
                trigger.attr('placeholder', i18n.loading + '...');
            }

            // Ajax lookup
            $.getJSONS3(url, function(data) {
                try {
                    self.data.id = data.id;
                    if (!opts.separateNameFields) {
                        var name = data.name;
                        trigger.val(name);
                        self.data.full_name = name;
                    }
                    self._processReponse(data);
                } catch(e) {
                    self._reset();
                }
                self.throbber.hide();
                trigger.removeAttr('placeholder');
            });
        },

        // --------------------------------------------------------------------
        /**
         * Ajax-search for possible duplicates
         */
        _checkDuplicates: function() {

            var opts = this.options,
                map = this._fieldMap(),
                selector = this.selector,
                current = this.data,
                data = {},
                value;

            if (current.id) {
                // User has selected an existing person
                // => no need to check for duplicates
                return;
            }

            // Collect the names
            if (opts.separateNameFields) {
                if (!current.first_name) {
                    return;
                }
                this.nameFields.forEach(function(fieldName) {
                    value = current[fieldName];
                    if (value) {
                        data[map[fieldName] || fieldName] = value;
                    }
                });
            } else {
                value = current.full_name;
                if (!value) {
                    return;
                }
                data.name = value;
            }

            // Collect the remaining fields
            this.personFields.forEach(function(fieldName) {
                value = current[fieldName];
                if (value) {
                    data[map[fieldName] || fieldName] = value;
                }
            });

            // @ToDo: Allow controller to be configurable
            var url = S3.Ap.concat('/pr/person/check_duplicates');
            $.ajaxS3({
                url: url,
                data: data,
                type: 'POST',
                dataType: 'json',
                success: function(data) {
                    // Remove old results
                    $(selector + '_results').remove();
                    if (data.length) {
                        // Display new count
                        var count = i18n.dupes_found.replace('_NUM_', data.length),
                            result = count + ' <i class="' + opts.downIcon + '"> </i>';
                        $(selector + '_duplicates').html(result)
                                                   .data('results', data)
                                                   .show();
                    } else {
                        // Clear old count
                        $(selector + '_duplicates').data('results', [])
                                                   .hide();
                    }
                }
            });
        },

        // --------------------------------------------------------------------
        /**
         * Display found duplicates
         */
        _displayDuplicates: function() {

            var opts = this.options,
                selector = this.selector;

            if ($(selector + '_results').length) {
                // Already showing
                return;
            }

            var cardLine = function(value, label) {
                var line = $('<div>').addClass('card_1_line');
                if (label) {
                    line.append($('<label>').html(label));
                }
                return line.append(/* $.parseHTML(value) */ value);
            };

            var cardButton = function(label, icon) {
                var button = $('<button type="button" class="fright">');
                if (icon) {
                    button.append($('<i class="' + icon + '">'));
                }
                return button.append(label);
            };

            var dupesCount = $(selector + '_duplicates'),
                items = dupesCount.data('results'),
                cardList = $('<div id="' + this.fieldName + '_results">'),
                card,
                name,
                picture,
                imagePath;

            items.forEach(function(item) {

                name = item.name;
                card = $('<div class="dl-item">').data({
                    'id': item.id,
                    'name': name
                });

                picture = $('<img width="50" height="50" class="media-object">');
                if (item.image) {
                    imagePath = '/default/download/' + item.image;
                } else {
                    imagePath = '/static/img/blank-user.gif';
                }
                picture.attr('src', S3.Ap.concat(imagePath));
                card.append($('<a class="fleft">').append(picture));

                if (item.org) {
                    card.append(cardLine(item.org));
                }

                card.append(cardLine(name));

                if (item.father_name && i18n.father_name_label) {
                    card.append(cardLine(item.father_name, i18n.father_name_label));
                }
                if (item.grandfather_name && i18n.grandfather_name_label) {
                    card.append(cardLine(item.grandfather_name, i18n.grandfather_name_label));
                }

                ['year_of_birth', 'dob', 'email', 'phone'].forEach(function(propName) {
                    var value = item[propName];
                    if (value) {
                        card.append(cardLine(value));
                    }
                });

                card.append(cardButton(i18n.Yes, opts.yesIcon));
                cardList.append(card);
            });

            var discard = $('<div class="dl-item">').append(cardButton(i18n.No, opts.noIcon));
            cardList.append(discard);

            dupesCount.after(cardList);

            // Scroll to this section
            $('html,body').animate({scrollTop: dupesCount.offset().top}, 250);
        },

        // --------------------------------------------------------------------
        /**
         * Handle selection of duplicate
         *
         * @param {integer} personID - the record ID of the selected item
         * @param {string} name - the full name in the selected item
         */
        _selectDuplicate: function(personID, name) {

            var selector = this.selector,
                dupesCount = $(selector + '_duplicates');

            if (personID && name) {
                // Yes: Select this person
                $(selector + '_full_name').val(name);

                // Remove results
                this._clearDuplicates();

                if (dupesCount.data('submit')) {
                    this.data = {'id': personID};
                    this._serialize();
                    dupesCount.closest('form').off(this.eventNamespace).submit();
                } else {
                    if (this.options.separateNameFields) {
                        this.trigger.val('');
                    }
                    this._selectPerson(personID);
                }
            } else {
                // No: Remove results
                this._clearDuplicates();

                if (dupesCount.data('submit')) {
                    dupesCount.closest('form').off(this.eventNamespace).submit();
                }
            }
        },

        // --------------------------------------------------------------------
        /**
         * Clear list of duplicates
         */
        _clearDuplicates: function() {

            var selector = this.selector;
            $(selector + '_duplicates').data('results', []).empty();
            $(selector + '_results').remove();
        },

        // --------------------------------------------------------------------
        /**
         * Actions upon form submission
         */
        _onFormSubmit: function(form) {

            var opts = this.options,
                selector = this.selector;

            if (opts.lookupDuplicates) {

                // Are there duplicates to be reviewed?
                var duplicates = $(selector + '_duplicates');
                if (duplicates.data('results').length) {

                    // Mark that form shall be submitted when the
                    // user has finished reviewing the duplicates
                    duplicates.data('submit', true);

                    // Display duplicates
                    this._displayDuplicates();

                    // Prevent form submission
                    return false;
                }
            }

            //S3ClearNavigateAwayConfirm();

            if (!this.data.id) {
                this._readInputs();
            } else {
                this.data = {'id': this.data.id};
            }
            this._serialize();

            $(form).off(this.eventNamespace).submit();

            return true;
        },

        // --------------------------------------------------------------------
        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var el = $(this.element),
                opts = this.options,
                selector = this.selector,
                ns = this.eventNamespace,
                self = this;

            // Form submission
            el.closest('form').on('submit' + ns, function(event) {
                event.preventDefault();
                return self._onFormSubmit(this);
            });

            // Edit and cancel actions
            $(selector + '_edit_bar .edit-action').on('click' + ns, function() {
                self._clearError();
                self._edit();
            });
            $(selector + '_edit_bar .cancel-action').on('click' + ns, function() {
                self._clearError();
                self._cancel();
            });

            // Filter Autocomplete-URL when selected organisation changes
            $(selector + '_organisation_id').change(function() {
                self.acURL = updateURLQuery(self.acURL, {
                    '~.organisation_id': $(this).val()
                });
            });

            // Remove error message when clicked on
            $(selector + '_title__row').next('.error_wrapper').one('click' + ns, function() {
                self._clearError();
                return false;
            });

            // Refresh this.data and search for duplicates whenever any
            // of the person fields are changed
            var fields = this.nameFields.concat(this.personFields);
            $(fields.map(function(fieldName) {
                return selector + '_' + fieldName;
            }).join(',')).on('change' + ns, function() {
                if (!self.data.id) {
                    self._readInputs();
                    self._serialize();
                    if (opts.lookupDuplicates) {
                        self._checkDuplicates();
                    }
                }
            });

            // Duplicate lookup
            if (opts.lookupDuplicates) {

                // Click-handler to show duplicate search results
                $(selector + '_duplicates').data('results', []).on('click' + ns, function() {
                    // Open up the full list of results
                    self._displayDuplicates();
                });

                // Handle duplicate selection
                // (delegated to form to catch future card insertions)
                el.closest('form').on('click' + ns, selector + '_results .dl-item', function() {
                    var $this = $(this),
                        personID = $this.data('id'),
                        name = $this.data('name');
                    self._selectDuplicate(personID, name);
                });

                // Clear duplicate search results when a person is selected
                el.on('change' + ns, function() {
                    if (el.val()) {
                        self._clearDuplicates();
                    }
                });
            }

            // ID Label lookup
            var idLabel = this.idLabel;
            if (idLabel) {

                // Typing into the ID label field triggers a lookup
                idLabel.on('input' + ns, function() {
                    var $this = $(this),
                        timer = $this.data('lookupTimeout');
                    if (timer) {
                        clearTimeout(timer);
                    }
                    timer = setTimeout(function() {
                        self.lookupIDLabel();
                    }, opts.delay);
                    $this.data('lookupTimeout', timer);
                });

                // Stepping out of the field cancels/prevents the lookup
                idLabel.on('blur' + this.eventNamespace, function() {
                    var $this = $(this),
                        lookup = $this.data('lookup'),
                        timer = $this.data('lookupTimeout');
                    if (lookup) {
                        lookup.abort();
                        $this.data('lookup', null);
                        self.idLabelThrobber.hide();
                    }
                    if (timer) {
                        clearTimeout(timer);
                    }
                });
            }

            return true;
        },

        // --------------------------------------------------------------------
        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var el = $(this.element),
                selector = this.selector,
                ns = this.eventNamespace;

            el.off(ns);
            el.closest('form').off(ns);

            $(selector + '_edit_bar .edit-action').off(ns);
            $(selector + '_edit_bar .cancel-action').off(ns);

            $(selector + '_duplicates').off(ns);

            var fields = this.nameFields.concat(this.personFields);
            $(fields.map(function(fieldName) {
                return selector + '_' + fieldName;
            }).join(',')).off(ns);

            var idLabel = this.idLabel;
            if (idLabel) {
                idLabel.off(ns);
            }

            return true;
        }
    });
})(jQuery);
