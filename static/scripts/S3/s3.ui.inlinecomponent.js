/**
 * jQuery UI InlineComponent Widget
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
    var inlinecomponentID = 0;

    /**
     * InlineComponent widget
     *
     * Terminology:
     *   - form          - refers to the outer form
     *   - input         - refers to the hidden INPUT in the outer form that
     *                     holds the JSON data for all rows inside this widget,
     *                     and will be processed server-side when the outer
     *                     form get submitted
     *   - widget        - refers to this widget
     *   - row, subform  - refers to one row inside the widget
     *   - field         - refers to a field inside a subform
     */
    $.widget('s3.inlinecomponent', {

        /**
         * Default options
         *
         * @todo implement/document options
         */
        options: {

        },

        /**
         * Create the widget
         */
        _create: function() {

            var el = $(this.element);

            this.id = inlinecomponentID;
            inlinecomponentID += 1;

            // Namespace for events
            this.namespace = '.inlinecomponent';
        },

        /**
         * Update the widget options
         */
        _init: function() {

            var el = $(this.element);

            this.formname = el.attr('id').split('-').pop();
            this.input = $('#' + el.attr('field'));

            // Configure layout-dependend functions
            var layout = this._layout;
            if ($.inlineComponentLayout) {
                // Use custom script
                layout = $.inlineComponentLayout;
            }
            this._renderReadRow = layout.renderReadRow;
            this._appendReadRow = layout.appendReadRow;
            this._appendError = layout.appendError;
            this._updateColumn = layout.updateColumn;

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

            var el = $(this.element);

            this._unbindEvents();

            this._openSingleRowSubforms();
            this._enforceRequired();

            this._bindEvents();
        },

        // Initialization -----------------------------------------------------

        /**
         * Automatically open single-row subform for editing,
         * and enforce add-row validation if it has defaults
         */
        _openSingleRowSubforms: function() {

            var el = $(this.element),
                self = this;

            el.find('.inline-form.read-row.single').each(function() {
                // Open edit-row by default
                var names = $(this).attr('id').split('-');
                var rowindex = names.pop(); // Will always be 0
                self._editRow(rowindex);
            });

            el.find('.inline-form.add-row.single').each(function() {
                // Check add-row for defaults
                var $row = $(this),
                    defaults = false;
                $row.find('input, select').each(function() {
                    var $this = $(this);
                    if ($this.val() && $this.attr('type') != 'checkbox') {
                        defaults = true;
                    }
                });
                if (defaults) {
                    // Enforce validation
                    self._markChanged($row);
                    self._catchSubmit($row);
                }
            });
        },

        /**
         * Enforce validation of required subforms
         */
        _enforceRequired: function() {

            var el = $(this.element),
                self = this;

            // Check for required subforms
            el.find('.inline-form.add-row.required').each(function() {
                // Ensure these get validated whether or not they are changed
                self._markChanged(this);
                self._catchSubmit(this);
            });
        },

        // Layout -------------------------------------------------------------

        /**
         * The default layout-dependend functions
         */
        _layout: {

            /**
            * Render a read-row (default row layout)
            *
            * @param {string} formname - the form name
            * @param {string|number} rowindex - the row index
            * @param {array} items - the data items
            *
            * @return {jQuery} the row
            */
            renderReadRow: function(formname, rowindex, items) {

                var columns = '';

                // Render the items
                for (var i=0, len=items.length; i<len; i++) {
                    columns += '<td>' + items[i] + '</td>';
                }

                // Append edit-button
                if ($('#edt-' + formname + '-none').length !== 0) {
                    columns += '<td><div><div id="edt-' + formname + '-' + rowindex + '" class="inline-edt"></div></div></td>';
                } else {
                    columns += '<td></td>';
                }

                // Append remove-button
                if ($('#rmv-' + formname + '-none').length !== 0) {
                    columns += '<td><div><div id="rmv-' + formname + '-' + rowindex + '" class="inline-rmv"></div></div></td>';
                } else {
                    columns += '<td></td>';
                }

                // Get the row
                var rowID = 'read-row-' + formname + '-' + rowindex;
                var row = $('#' + rowID);
                if (!row.length) {
                    // New row
                    row = $('<tr id="' + rowID + '" class="read-row">');
                }

                // Add the columns to the row
                row.empty().html(columns);

                return row;
            },

            /**
             * Append a new read-row to the inline component
             *
             * @param {string} formname - the formname
             * @param {jQuery} row - the row to append
             */
            appendReadRow: function(formname, row) {

                $('#sub-' + formname + ' > table.embeddedComponent > tbody').append(row);
            },

            /**
            * Append an error to a form field or row
            *
            * @param {string} formname - the form name
            * @param {string|number} rowindex - the input row index ('none' for add, '0' for edit)
            * @param {string} fieldname - the field name
            * @param {string} message - the error message
            */
            appendError: function(formname, rowindex, fieldname, message) {

                var errorClass = formname + '_error',
                    target,
                    msg = '<div class="error">' + message + '</div>';

                if (null === fieldname) {
                    // Append error message to the whole subform
                    if ('none' == rowindex) {
                        target = '#add-row-' + formname;
                    } else {
                        target = '#edit-row-' + formname;
                    }
                    msg = $('<tr><td colspan="' + $(target + '> td').length + '">' + msg + '</td></tr>');
                } else {
                    // Append error message to subform field
                    target = '#sub_' + formname + '_' + formname + '_i_' + fieldname + '_edit_' + rowindex;
                    msg = $(msg);
                }
                msg.addClass(errorClass).hide().insertAfter(target);
            },

            /**
            * Update (replace) the content of a column, needed to write
            * read-only field data into an edit row
            *
            * @param {jQuery} row - the row
            * @param {number} colIndex - the column index
            * @param {string|HTML} contents - the column contents
            */
            updateColumn: function(row, colIndex, contents) {

                $(row).find('td').eq(colIndex).html(contents);
            }
        },

        // Utilities ----------------------------------------------------------

        /**
         * Mark a row as changed
         *
         * @param {jQuery} element - the trigger element
         */
        _markChanged: function(element) {

            $(element).closest('.inline-form').addClass('changed');
        },

        /**
         * Parse the JSON from the real input, and bind the result
         * as 'data' object to the real input
         *
         * @return {object} the data object
         */
        _deserialize: function() {

            var input = this.input;

            var data = JSON.parse(input.val());
            input.data('data', data);

            return data;
        },

        /**
         * Serialize the 'data' object of the real input as JSON and
         * set the JSON as value for the real input
         *
         * @return {string} the JSON
         */
        _serialize: function() {

            var input = this.input;

            var json = JSON.stringify(input.data('data'));
            input.val(json);

            return json;
        },

        /**
         * Display all errors
         */
        _displayErrors: function() {
            $('.' + this.formname + '_error').show();
        },

        /**
         * Remove all error messages from all rows
         */
        _removeErrors: function() {
            $('.' + this.formname + '_error').remove();
        },

        /**
         * Disable the add-row
         */
        _disableAddRow: function() {

            var addRow = $('#add-row-' + this.formname);
            addRow.find('input, select, textarea').prop('disabled', true);
            addRow.find('.inline-add, .action-lnk').addClass('hide');
        },

        /**
         * Enable the add-row
         */
        _enableAddRow: function() {

            var addRow = $('#add-row-' + this.formname);
            addRow.find('input, select, textarea').prop('disabled', false);
            addRow.find('.inline-add, .action-lnk').removeClass('hide');
        },

        /**
         * Ensure that all inline forms are checked upon submission of
         * main form
         *
         * @param {jQuery} element - the trigger element
         */
        _catchSubmit: function(element) {

            var ns = this.namespace + this.id;
            $(this.element).closest('form')
                           .unbind(ns)
                           .bind('submit' + ns, {widget: this}, this._submitAll);
        },

        // Data Processing and Validation -------------------------------------

        /**
         * Collect the data from the form
         *
         * @param {object} data - the de-serialized JSON data
         * @param {string|number} rowindex - the row index
         */
        _collectData: function(data, rowindex) {

            var formname = this.formname;

            // Retain the original record ID
            var rows = data['data'];
            var original = rows[rowindex];
            var row = {};
            if (typeof original != 'undefined') {
                var record_id = original['_id'];
                if (typeof record_id != 'undefined') {
                    row['_id'] = record_id;
                }
            }

            // Collect the input data
            var fieldname,
                selector,
                input,
                value,
                cssclass,
                intvalue,
                fields = data['fields'],
                upload_index;
            for (var i=0; i < fields.length; i++) {
                fieldname = fields[i]['name'];
                selector = '#sub_' + formname + '_' + formname + '_i_' + fieldname + '_edit_' + rowindex;
                input = $(selector);
                if (input.length) {
                    // Field is Writable
                    value = input.val();
                    if (input.attr('type') == 'file') {
                        // Clone the Input ready to accept new files
                        var cloned = input.clone();
                        cloned.insertAfter(input);
                        // Store the original input at the end of the form
                        // - we move the original input as it doesn't contain the file otherwise on IE, etc
                        // http://stackoverflow.com/questions/415483/clone-a-file-input-element-in-javascript
                        var add_button = $('#add-' + formname + '-' + rowindex),
                            multiple;
                        if (add_button.length) {
                            multiple = true;
                        } else {
                            // Only one row can exist & this must be added during form submission
                            multiple = false;
                        }
                        if (!multiple && rowindex == 'none') {
                            upload_index = '0';
                        } else {
                            upload_index = rowindex;
                        }
                        var upload_id = 'upload_' + formname + '_' + fieldname + '_' + upload_index;
                        // Remove any old upload for this index
                        $('#' + upload_id).remove();
                        var form = input.closest('form');
                        input.css({display: 'none'})
                            .attr('id', upload_id)
                            .attr('name', upload_id)
                            .appendTo(form);
                        if (value.match(/fakepath/)) {
                            // IE, etc: Remove 'fakepath' from filename
                            value = value.replace(/(c:\\)*fakepath\\/i, '');
                        }
                    } else if (input.attr('type') == 'checkbox') {
                        value = input.prop('checked');
                    } else {
                        cssclass = input.attr('class');
                        if (cssclass == 'generic-widget') {
                            // Reference values need to be ints for S3Represent to find a match in theset
                            // - ensure we don't do this to dates though!
                            intvalue = parseInt(value, 10);
                            if (!isNaN(intvalue)) {
                                value = intvalue;
                            }
                        }
                    }
                } else {
                    // Field is Read-only
                    if (typeof original != 'undefined') {
                        // Keep current value
                        value = original[fieldname]['value'];
                    } else {
                        value = '';
                    }
                }
                row[fieldname] = value;
            }

            var single = $('#read-row-' + formname + '-' + rowindex).hasClass('single');
            if (single) {
                // A multiple=False subform being edited
                // => setting all fields to '' indicates delete
                var deleteRow = true;
                for (fieldname in row) {
                    if ((fieldname != '_id') && (row[fieldname] !== '')) {
                        deleteRow = false;
                        break;
                    }
                }
                if (deleteRow) {
                    // Check whether subform is required
                    var required = $('#edit-row-' + formname).hasClass('required');
                    if (required) {
                        // Subform is required => cannot delete
                        this._appendError(formname, '0', fieldname, i18n.enter_value);
                        row['_error'] = true;
                    } else {
                        // Delete it
                        row['_delete'] = true;
                    }
                } else {
                    delete row['_error'];
                }
            } else {
                // Check whether subform is required
                var subformRequired = false;
                if ($('#add-row-' + formname).hasClass('required') ||
                    $('#edit-row-' + formname).hasClass('required')) {
                    subformRequired = true;
                }
                // Make sure there is at least one row
                if (subformRequired) {
                    // Check if empty
                    delete row['_error'];
                    var empty = true;
                    for (fieldname in row) {
                        if ((fieldname != '_id') && (row[fieldname] !== '')) {
                            empty = false;
                        }
                    }
                    if (empty) {
                        var errorIndex = 'none';
                        if (rowindex != 'none') {
                            // This is the edit-row, so the index is always '0'
                            errorIndex = '0';
                        }
                        // Check whether rows can be added (=whether there is an add-button)
                        if ($('#add-' + formname + '-' + rowindex).length) {
                            // Multiple=true, rows can be added
                            if (!$('#read-row-' + formname + '-0').length) {
                                // No rows present => error
                                this._appendError(formname, errorIndex, fieldname, i18n.enter_value);
                                row['_error'] = true;
                            }
                        } else {
                            // Multiple=false, no other rows can exist => error
                            this._appendError(formname, errorIndex, fieldname, i18n.enter_value);
                            row['_error'] = true;
                        }
                    }
                }
            }

            // Add the defaults
            var defaults = data['defaults'];
            for (fieldname in defaults) {
                if (!row.hasOwnProperty(fieldname)) {
                    value = defaults[fieldname]['value'];
                    row[fieldname] = value;
                }
            }

            // Return the row object
            return row;
        },

        /**
         * Validate a new/updated row
         *
         * @param {string|number} rowindex - the input row index ('none' for add, '0' for edit)
         * @param {object} data - the de-serialized JSON data
         * @param {object} row - the new row data
         */
        _validate: function(data, rowindex, row) {

            var formname = this.formname;

            if (row._error) {
                // Required row which has already been validated as bad
                this._displayErrors();
                return null;
            }

            // Construct the URL
            var c = data['controller'],
                f = data['function'],
                resource = data['resource'],
                component = data['component'];
            var url = S3.Ap.concat('/' + c + '/' + f + '/validate.json'),
                concat;
            if (null !== resource && typeof resource != 'undefined') {
                url += '?resource=' + resource;
                concat = '&';
            } else {
                concat = '?';
            }
            if (null !== component && typeof component != 'undefined') {
                url += concat + 'component=' + component;
            }

            // Request validation of the row
            // @ToDo: Skip read-only fields (especially Virtual)
            var row_json = JSON.stringify(row),
                response = null;
            $.ajaxS3({
                async: false,
                type: 'POST',
                url: url,
                data: row_json,
                dataType: 'json',
                contentType: 'application/json; charset=utf-8',
                // gets moved to .done() inside .ajaxS3
                success: function(data) {
                    response = data;
                }
            });

            // Check and report errors
            var has_errors = false;
            if (!response) {
                has_errors = true;
            } else if (response.hasOwnProperty('_error')) {
                has_errors = true;
                this._appendError(formname, rowindex, null, response._error);
            }
            var item,
                error,
                field;
            for (field in response) {
                item = response[field];
                if (item.hasOwnProperty('_error')) {
                    error = item._error;
                    if (error == "invalid field") {
                        // Virtual Field - not a real error
                        item.text = item.value;
                    } else {
                        this._appendError(formname, rowindex, field, error);
                        has_errors = true;
                    }
                }
            }

            // Return the validated + represented row
            // (or null if there was an error)
            if (has_errors) {
                this._displayErrors();
                return null;
            } else {
                return response;
            }
        },

        // Form Actions -------------------------------------------------------

        /**
         * Edit a row
         *
         * @param {string|number} rowindex - the row index
         *
         * @todo: separate out the update of the read-row
         */
        _editRow: function(rowindex) {

            var formname = this.formname;
            var rowname = formname + '-' + rowindex;

            this._removeErrors();

            // Show all read rows for this field
            $('#sub-' + formname + ' .read-row').removeClass('hide');
            // Hide the current read row, unless it's an Image
            if (formname != 'imageimage') {
                $('#read-row-' + rowname).addClass('hide');
            }

            // Populate the edit row with the data for this rowindex
            var data = this._deserialize();
            var fields = data['fields'];
            var row = data['data'][rowindex];
            var fieldname,
                element,
                input,
                text,
                value,
                i;
            for (i=0; i < fields.length; i++) {
                fieldname = fields[i]['name'];
                value = row[fieldname]['value'];
                element = '#sub_' + formname + '_' + formname + '_i_' + fieldname + '_edit_0';
                // If the element is a select then we may need to add the option we're choosing
                var select = $('select' + element);
                if (select.length !== 0) {
                    var option = $('select' + element + ' option[value="' + value + '"]');
                    if (option.length === 0) {
                        // This option does not exist in the select, so add it
                        // because otherwise val() won't work. Maybe the option
                        // gets added later by a script (e.g. S3OptionsFilter)
                        select.append('<option value="' + value + '">-</option>');
                    }
                }
                input = $(element);
                if (!input.length) {
                    // Read-only field
                    this._updateColumn($('#edit-row-' + formname), i, row[fieldname]['text']);
                } else {
                    if (input.attr('type') == 'file') {
                        // Update the existing upload item, if there is one
                        var upload = $('#upload_' + formname + '_' + fieldname + '_' + rowindex);
                        if (upload.length) {
                            var id = input.attr('id');
                            var name = input.attr('name');
                            input.replaceWith(upload);
                            upload.attr('id', id)
                                  .attr('name', name)
                                  .css({display: ''});
                        }
                    } else if (input.attr('type') == 'checkbox') {
                        input.prop('checked', value);
                    } else {
                        input.val(value);
                        if (input.hasClass('multiselect-widget') && input.multiselect('instance')) {
                            input.multiselect('refresh');
                        } else if (input.hasClass('groupedopts-widget') && input.groupedopts('instance')) {
                            input.groupedopts('refresh');
                        } else if (input.hasClass('location-selector') && input.locationselector('instance')) {
                            input.locationselector('refresh');
                        } else {
                            // Populate text in autocompletes
                            element = '#dummy_sub_' + formname + '_' + formname + '_i_' + fieldname + '_edit_0';
                            text = row[fieldname]['text'];
                            $(element).val(text);
                        }
                    }
                }
            }

            // Insert the edit row after this read row
            var edit_row = $('#edit-row-' + formname);
            edit_row.insertAfter('#read-row-' + rowname);

            // Remember the current row index in the edit row & show it
            edit_row.data('rowindex', rowindex)
                    .removeClass('hide');

            // Trigger the dropdown change event
            $('#edit-row-' + formname + ' select:not(".lx-select")').change();

            // Disable the add-row while editing
            this._disableAddRow();
        },

        /**
         * Cancel editing a row
         *
         * @param {string|number} rowindex - the row index
         */
        _cancelEdit: function(rowindex) {

            var formname = this.formname;
            var rowname = formname + '-' + rowindex;

            this._removeErrors();

            var edit_row = $('#edit-row-' + formname);

            // Hide and reset the edit-row
            edit_row.addClass('hide')
                    .data('rowindex', null)
                    .removeClass('changed');

            // Show the read-row
            $('#read-row-' + rowname).removeClass('hide');

            // Enable the add-row
            this._enableAddRow();
        },

        /**
         * Add a new row
         *
         * @todo: separate out the creation of a new read-row
         */
        _addRow: function() {

            var formname = this.formname;
            var rowindex = 'none';

            var add_button = $('#add-' + formname + '-' + rowindex),
                multiple;
            if (add_button.length) {
                multiple = true;
            } else {
                // Only one row can exist & this must be added during form submission
                multiple = false;
            }

            if (multiple) {
                // Hide add-button, show throbber
                add_button.addClass('hide');
                var throbber = $('#throbber-' + formname + '-' + rowindex);
                throbber.removeClass('hide');

                // Remove any previous error messages
                this._removeErrors();
            }

            // Collect the values from the add-row
            var data = this._deserialize();
            var row_data = this._collectData(data, 'none');

            // If this is an empty required=true row in a multiple=true with existing rows, then don't validate
            var add_required = $('#add-row-' + formname).hasClass('required'),
                empty,
                fieldname;
            if (add_required) {
                empty = true;
                for (fieldname in row_data) {
                    if ((fieldname != '_id') && (row_data[fieldname] !== '')) {
                        empty = false;
                    }
                }
                if (empty) {
                    // Check if we have other rows
                    if ($('#add-' + formname + '-' + rowindex).length) {
                        // multiple=true, can have other rows
                        if ($('#read-row-' + formname + '-0').length) {
                            // Rows present, so skip validation
                            // Hide throbber, show add-button
                            throbber.addClass('hide');
                            add_button.removeClass('hide');
                            return true;
                        }
                    }
                }
            }

            // Validate the data
            var new_row = this._validate(data, rowindex, row_data);

            var success = false;
            if (null !== new_row) {
                success = true;
                // Add a new row to the real_input JSON
                new_row['_changed'] = true; // mark as changed
                var newindex = data['data'].push(new_row) - 1;
                new_row['_index'] = newindex;
                this._serialize();

                if (multiple) {
                    // Create a new read-row, clear add-row
                    var items = [],
                        fields = data['fields'],
                        i,
                        field,
                        upload,
                        d,
                        f,
                        default_value;
                    for (i=0; i < fields.length; i++) {
                        field = fields[i]['name'];
                        // Update all uploads to the new index
                        upload = $('#upload_' + formname + '_' + field + '_none');
                        if (upload.length) {
                            var upload_id = 'upload_' + formname + '_' + field + '_' + newindex;
                            $('#' + upload_id).remove();
                            upload.attr('id', upload_id)
                                .attr('name', upload_id);
                        }
                        items.push(new_row[field]['text']);
                        // Reset add-field to default value
                        d = $('#sub_' + formname + '_' + formname + '_i_' + field + '_edit_default');
                        f = $('#sub_' + formname + '_' + formname + '_i_' + field + '_edit_none');
                        if (f.attr('type') == 'file') {
                            var self = this,
                                emptyWidget = d.clone();
                            emptyWidget.attr('id', f.attr('id'))
                                       .attr('name', f.attr('name'))
                                       // Set event onto new input to Mark row changed when new files uploaded
                                       .change(function() {
                                self._markChanged(this);
                                self._catchSubmit(this);
                            });
                            f.replaceWith(emptyWidget);
                        } else {
                            default_value = d.val();
                            f.val(default_value);
                            // Update widgets
                            if (f.attr('type') == 'checkbox') {
                                f.prop('checked', d.prop('checked'));
                            } else if (f.hasClass('multiselect-widget') && f.multiselect('instance')) {
                                f.multiselect('refresh');
                            } else if (f.hasClass('groupedopts-widget') && f.groupedopts('instance')) {
                                f.groupedopts('refresh');
                            } else if (f.hasClass('location-selector') && f.locationselector('instance')) {
                                f.locationselector('refresh');
                            }
                        }
                        default_value = $('#dummy_sub_' + formname + '_' + formname + '_i_' + field + '_edit_default').val();
                        $('#dummy_sub_' + formname + '_' + formname + '_i_' + field + '_edit_none').val(default_value);
                    }
                    // Unmark changed
                    $('#add-row-' + formname).removeClass('changed');

                    // Render new read row and append to container
                    var read_row = this._renderReadRow(formname, newindex, items);

                    // Append read-row
                    this._appendReadRow(formname, read_row);
                }
            }

            if (multiple) {
                // Hide throbber, show add-button
                throbber.addClass('hide');
                add_button.removeClass('hide');
            }
            if (success) {
                $(this.element).closest('form').unbind(this.namespace + this.id);
            }

            return success;
        },

        /**
         * Update row
         *
         * @param {string|number} rowindex - the row index
         */
        _updateRow: function(rowindex) {

            var formname = this.formname;
            var rowname = formname + '-' + rowindex;

            var rdy = $('#rdy-' + formname + '-0'),
                multiple;
            if (rdy.length) {
                multiple = true;
            } else {
                // Only one row can exist & this must be updated during form submission
                multiple = false;
            }

            if (multiple) {
                // Hide rdy, show throbber
                rdy.addClass('hide');
                var throbber = $('#throbber-' + formname + '-0');
                throbber.removeClass('hide');

                // Remove any previous error messages
                this._removeErrors();
            }

            // Collect the values from the edit-row
            var data = this._deserialize();
            var row_data = this._collectData(data, '0');

            if (row_data['_delete']) {

                // multiple=False form which has set all fields to '' to delete the row
                data['data'][rowindex]['_delete'] = true;
                this._serialize();
                return true;

            } else {
                // Validate the form data
                var new_row = this._validate(data, '0', row_data);

                var success = false;
                if (null !== new_row) {
                    success = true;

                    // Update the row in the real_input JSON
                    new_row['_id'] = data['data'][rowindex]['_id'];
                    new_row['_changed'] = true; // mark as changed
                    new_row['_index'] = rowindex;
                    data['data'][rowindex] = new_row;
                    this._serialize();

                    if (multiple) {
                        // Update read-row in the table, clear edit-row
                        var items = [],
                            fields = data['fields'],
                            default_value,
                            i;
                        for (i=0; i < fields.length; i++) {
                            var field = fields[i]['name'];
                            items.push(new_row[field]['text']);
                            // Reset edit-field to default value
                            var d = $('#sub_' + formname + '_' + formname + '_i_' + field + '_edit_default');
                            var f = $('#sub_' + formname + '_' + formname + '_i_' + field + '_edit_0');
                            if (f.attr('type') == 'file') {
                                var empty = d.clone(),
                                    self = this;
                                empty.attr('id', f.attr('id'))
                                    .attr('name', f.attr('name'))
                                    // Set event onto new input to Mark row changed when new files uploaded
                                    .change(function() {
                                    self._markChanged(this);
                                    self._catchSubmit(this);
                                });
                                f.replaceWith(empty);
                            } else {
                                default_value = d.val();
                                f.val(default_value);
                            }
                            default_value = $('#dummy_sub_' + formname + '_' + formname + '_i_' + field + '_edit_default').val();
                            $('#dummy_sub_' + formname + '_' + formname + '_i_' + field + '_edit_0').val(default_value);
                        }
                        // Unmark changed
                        var edit_row = $('#edit-row-' + formname);
                        edit_row.removeClass('changed');

                        // Update the read row
                        var read_row = this._renderReadRow(formname, rowindex, items);

                        // Hide and reset the edit row
                        edit_row.addClass('hide')
                                // Reset rowindex
                                .data('rowindex', null);

                        // Show the read row
                        read_row.removeClass('hide');

                        // Re-enable add-row
                        this._enableAddRow();
                    }
                }

                if (multiple) {
                    // Hide throbber, enable rdy
                    rdy.removeClass('hide');
                    throbber.addClass('hide');
                }

                return (success);
            }
        },

        /**
         * Remove a row
         *
         * @param {string|number} rowindex - the row index
         */
        _removeRow: function(rowindex) {

            var formname = this.formname;
            var rowname = formname + '-' + rowindex;

            // Confirmation dialog
            if (!confirm(i18n.delete_confirmation)) {
                return false;
            }

            // Update the real_input JSON with deletion of this row
            var data = this._deserialize();
            data['data'][rowindex]['_delete'] = true;
            this._serialize();

            // Remove the read-row for this item
            $('#read-row-' + rowname).remove();

            // Remove all uploads for this item
            $('input[name^="' + 'upload_' + formname + '_"][name$="_' + rowindex + '"]').remove();

            var edit_row = $('#edit-row-' + formname);
            if (edit_row.hasClass('required')) {
                if (!$('#read-row-' + formname + '-0').length) {
                    // No more rows present - set the add row as required
                    $('#add-row-' + formname).addClass('required');
                    edit_row.removeClass('required');
                    // Ensure we validate this if not changed
                    this._catchSubmit(edit_row);
                }
            }

            return true;
        },

        // Event Handlers -----------------------------------------------------

        /**
         * Submit all changed inline-rows, and then the outer form
         *
         * @param {event} event - the submit-event (scope = outer form)
         */
        _submitAll: function(event) {

            var self = event.data.widget;

            event.preventDefault();

            var el = $(self.element),
                empty,
                success,
                errors = false,
                row;

            // Find and validate all pending rows
            var rows = el.find('.inline-form.changed, .inline-form.required');
            for (var i=0, len=rows.length; i < len; i++) {

                row = $(rows[i]);
                empty = true;
                if (!row.hasClass('required')) {
                    // Check that the row contains data
                    var inputs = row.find('input, select, textarea'),
                        input;
                    for (var j=0, numfields=inputs.length; j < numfields; i++) {
                        input = $(inputs[j]);
                        if ((input.attr('type') != 'checkbox' && input.val()) || input.prop('checked')) {
                            empty = false;
                            break;
                        }
                    }
                } else {
                    // Treat required rows as non-empty
                    empty = false;
                }
                // Validate all non-empty rows
                if (!empty) {
                    if (row.hasClass('add-row')) {
                        success = self._addRow();
                    } else {
                        success = self._updateRow(row.data('rowindex'));
                    }
                    if (!success) {
                        errors = true;
                    }
                }
            }
            if (!errors) {
                // Remove the submit-event handler for this widget and
                // continue submitting the main form (=this)
                $(this).unbind(self.namespace + self.id).submit();
            }
        },

        /**
         * S3SQLInlineComponentCheckbox: status update after form error
         */
        _updateCheckboxStatus: function() {

            var el = $(this.element),
                self = this,
                checkbox,
                fieldname,
                value,
                data,
                row;

            el.find(':checkbox').each(function() {

                checkbox = $(this);

                fieldname = checkbox.attr('id').split('-')[2];
                value = checkbox.val();

                // Read current data from real input
                data = self._deserialize()['data'];

                // Find the corresponding data item
                for (var i=0, len=data.length; i < len; i++) {
                    row = data[i];
                    if (row.hasOwnProperty(fieldname) && row[fieldname].value == value) {
                        // Modify checkbox state, as-required
                        if (row._changed) {
                            checkbox.prop('checked', true);
                        } else if (row._delete) {
                            checkbox.prop('checked', false);
                        }
                        break;
                    }
                }
            });
        },

        /**
         * S3SQLInlineComponentCheckbox: click-event handler
         *
         * @param {event} event - the click event
         */
        _checkboxOnClick: function(event) {

            var self = event.data.widget,
                checkbox = $(this);

            var fieldname = checkbox.attr('id').split('-')[2],
                value = checkbox.val(),
                item = null,
                row;

            // Read current data from real input
            var data = self._deserialize().data;

            // Find the corresponding data item
            for (var i=0, len=data.length; i < len; i++) {
                row = data[i];
                if (row.hasOwnProperty(fieldname) && row[fieldname].value == value) {
                    item = row;
                    break;
                }
            }

            // Modify data
            if (checkbox.prop('checked')) {
                if (!item) {
                    // Not yet found, so initialise
                    var label = checkbox.next().html(); // May be fragile to different formstyles :/
                    item = {};
                    item[fieldname] = {'text': label, 'value': value};
                    data.push(item);
                }
                item._changed = true;
                // Remove delete-marker if re-selected
                if (item.hasOwnProperty('_delete')) {
                    delete item._delete;
                }
            } else if (item) {
                item._delete = true;
            }

            // Write data back to real input
            self._serialize();
        },

        /**
         * S3SQLInlineComponentMultiSelectWidget: change-event handler
         *
         * @param {event} event - the change event
         */
        _multiselectOnChange: function(event) {

            var self = event.data.widget,
                multiselect = $(this);

            var fieldname = multiselect.attr('id').split('-')[1],
                values = multiselect.val(),
                row,
                item,
                label,
                value;

            // Read current data from real input
            var data = self._deserialize().data;

            // Update current items
            var current_items = [],
                i,
                len;
            for (i=0, len=data.length; i < len; i++) {
                row = data[i];
                if (row.hasOwnProperty(fieldname)) {
                    value = row[fieldname].value.toString();
                    if ($.inArray(value, values) == -1) {
                        // No longer selected => mark for delete
                        row._delete = true;
                    } else {
                        // Remove delete-marker if re-selected
                        if (row.hasOwnProperty('_delete')) {
                            delete row._delete;
                        }
                    }
                    current_items.push(value);
                }
            }

            // Add new items
            var new_items = $(values).not(current_items).get();
            for (i=0, len=new_items.length; i < len; i++) {
                value = new_items[i];
                label = multiselect.find('option[value=' + value + ']').html();
                item = {};
                item[fieldname] = {'text': label, 'value': value};
                item._changed = true;
                if (row.hasOwnProperty('_delete')) {
                    delete row._delete;
                }
                data.push(item);
            }

            // Write data back to real input
            self._serialize();
        },

        /**
         * S3LocationSelectorWidget2: change-event handler
         *
         * @param {event} event - the change event
         */
        _locationSelectorOnChange: function(event) {

            var self = event.data.widget;

            var $this = $(this);
            var names = $this.attr('id').split('_');
            var formname = names[1];

            // @ToDo: Handle multiple=True
            // - add-row always visible
            // - delete
            // - represent
            if ($('#add-row-' + formname).is(':visible')) {
                // Don't do anything if we're in a Create row as we'll be processed on form submission
                return;
            }
            var fieldname = names[4] + '_' + names[5];

            // Read current data from real input
            var data = self._deserialize().data;

            var new_value = $this.val(),
                old_value,
                item,
                found = false;
            for (var prop in data) {
                item = data[prop];
                if (item.hasOwnProperty(fieldname)) {
                    found = true;
                    old_value = item[fieldname].value;
                    if (old_value) {
                        old_value = old_value.toString();
                    }
                    break;
                }
            }

            var represent;
            if (found && (new_value != old_value)) {
                // Modify the Data
                item[fieldname].value = new_value;
                // Calculate represent from Street Address or lowest-Lx.
                // Only needed when we support multiple=True
                represent = 'todo';
                item[fieldname].text = represent;
                item._changed = true;
            } else if (new_value) {
                // Add a New Item
                item = {};
                represent = 'todo';
                item[fieldname] = {'text': represent, 'value': new_value};
                item._changed = true;
                data.push(item);
            }

            // Write data back to real input
            self._serialize();
        },

        // Event Management ---------------------------------------------------

        /**
         * Bind event handlers (after refresh)
         */
        _bindEvents: function() {

            var el = $(this.element),
                ns = this.namespace,
                self = this;

            // Button events
            el.delegate('.read-row', 'click' + ns, function() {
                var names = $(this).attr('id').split('-');
                var rowindex = names.pop();
                self._editRow(rowindex);
                return false;
            }).delegate('.inline-add', 'click' + ns, function() {
                self._addRow();
                return false;
            }).delegate('.inline-cnc', 'click' + ns, function() {
                var names = $(this).attr('id').split('-');
                var zero = names.pop();
                var formname = names.pop();
                var rowindex = $('#edit-row-' + formname).data('rowindex');
                self._cancelEdit(rowindex);
                return false;
            }).delegate('.inline-rdy', 'click' + ns, function() {
                var names = $(this).attr('id').split('-');
                var zero = names.pop();
                var formname = names.pop();
                var rowindex = $('#edit-row-' + formname).data('rowindex');
                self._updateRow(rowindex);
                return false;
            }).delegate('.inline-edt', 'click' + ns, function() {
                var names = $(this).attr('id').split('-');
                var rowindex = names.pop();
                self._editRow(rowindex);
                return false;
            }).delegate('.inline-rmv', 'click' + ns, function() {
                var names = $(this).attr('id').split('-');
                var rowindex = names.pop();
                self._removeRow(rowindex);
                return false;
            }).delegate('.error', 'click' + ns, function() {
                $(this).fadeOut('medium', function() { $(this).remove(); });
                return false;
            });

            // Form events
            var inputs = 'input',
                textInputs = 'input[type="text"],input[type="file"],textarea',
                fileInputs = 'input[type="file"]',
                otherInputs = 'input[type!="text"][type!="file"],select',
                multiSelects = 'select.multiselect-widget';

            el.find('.add-row,.edit-row').each(function() {
                var $this = $(this);
                $this.find(textInputs).bind('input' + ns, function() {
                    self._markChanged(this);
                    self._catchSubmit(this);
                });
                $this.find(fileInputs).bind('change' + ns, function() {
                    self._markChanged(this);
                    self._catchSubmit(this);
                });
                $this.find(otherInputs).bind('focusin' + ns, function() {
                    $(this).one('change' + ns, function() {
                        self._markChanged(this);
                        self._catchSubmit(this);
                    }).one('focusout', function() {
                        $(this).unbind('change' + ns);
                    });
                });
                $this.find(multiSelects).bind('multiselectopen' + ns, function() {
                    $(this).unbind('change' + ns)
                           .one('change' + ns, function() {
                        self._markChanged(this);
                        self._catchSubmit(this);
                    });
                });
                $this.find(inputs).bind('keypress' + ns, function(e) {
                    if (e.which == 13) {
                        e.preventDefault();
                        return false;
                    }
                    return true;
                });
            });

            el.find('.add-row').each(function() {
                $(this).find(inputs).bind('keyup' + ns, function(e) {
                    switch (e.which) {
                        case 13: // Enter
                            self._addRow();
                            break;
                        default:
                            break;
                    }
                });
            });

            el.find('.edit-row').each(function() {
                $(this).find(inputs).bind('keyup' + ns, function(e) {
                    var rowIndex = $(this).closest('.edit-row').data('rowindex');
                    switch (e.which) {
                        case 13: // Enter
                            self._updateRow(rowIndex);
                            break;
                        case 27: // Escape
                            self._cancelEdit(rowIndex);
                            break;
                        default:
                            break;
                    }
                });
            });

            // Event Management for S3SQLInlineComponentCheckbox
            if (el.hasClass('inline-checkbox')) {
                var error_wrapper = $(this.element).closest('form')
                                                   .find('.error_wrapper');
                if (error_wrapper.length) {
                    this._updateCheckboxStatus();
                }
                // Delegate click-event, so that it also applies for
                // dynamically inserted checkboxes
                el.delegate(':checkbox', 'click' + ns, {widget: this}, this._checkboxOnClick);
            }

            // Event Management for S3SQLInlineComponentMultiSelectWidget
            if (el.hasClass('inline-multiselect')) {
                el.find('.inline-multiselect-widget')
                  .bind('change' + ns, {widget: this}, this._multiselectOnChange);
            }

            // Event Management for S3LocationSelectorWidget2
            el.find('.inline-locationselector-widget')
              .bind('change' + ns, {widget: this}, this._locationSelectorOnChange);

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var el = $(this.element),
                ns = this.namespace;

            // Remove inline-multiselect-widget event handlers
            if (el.hasClass('inline-multiselect')) {
                el.find('.inline-multiselect-widget')
                  .unbind(ns);
            }

            // Remove inline-locationselector-widget event handlers
            el.find('.inline-locationselector-widget')
              .unbind(ns);

            // Remove all form event handlers
            el.find('.add-row,.edit-row').each(function() {
                $(this).find('input,textarea,select').unbind(ns);
            });

            // Remove all delegations
            el.undelegate(ns);

            return true;
        }
    });
})(jQuery);

$(document).ready(function() {
    // Activate on all inline-components in the current page
    $('.inline-component').inlinecomponent({});
});
