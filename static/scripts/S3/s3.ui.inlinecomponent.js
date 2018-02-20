/**
 * jQuery UI InlineComponent Widget
 *
 * @copyright 2015-2018 (c) Sahana Software Foundation
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

            this.id = inlinecomponentID;
            inlinecomponentID += 1;

            // Namespace for events
            this.eventNamespace = '.inlinecomponent';
        },

        /**
         * Update the widget options
         */
        _init: function() {

            var el = $(this.element);

            this.formname = el.attr('id').split('-').pop();
            this.input = $('#' + el.attr('field'));

            // Configure layout-dependent functions
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

            this._unbindEvents();

            this._openSingleRowSubforms();
            this._enforceRequired();

            // Find non-static header rows
            this.labelRow = $('#sub-' + this.formname + ' .label-row:not(.static)');

            // Hide discard action in add-row unless explicitAdd
            if (!$(this.element).find('.inline-open-add').length) {
                $('#add-row-' + this.formname + ' .inline-dsc').hide();
            }

            this._showHeaders();
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
                var names = $(this).attr('id').split('-'),
                    rowindex = names.pop(); // Will always be 0
                self._editRow(rowindex);
            });

            el.find('.inline-form.add-row.single').each(function() {
                // Check add-row for defaults
                var $row = $(this),
                    defaults = false;

                $row.find('input[type!="hidden"], select, textarea').each(function() {
                    var $this = $(this),
                        visible = $this.css('display') != 'none';
                    if (visible && $this.val() && $this.attr('type') != 'checkbox') {
                        defaults = true;
                    }
                });

                if (defaults) {
                    // Enforce validation
                    self._markChanged($row);
                    self._catchSubmit();
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
                self._catchSubmit();
            });
        },

        // Layout -------------------------------------------------------------

        /**
         * The default layout-dependent functions
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
                var rowID = 'read-row-' + formname + '-' + rowindex,
                    row = $('#' + rowID);
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
                    msg = '<div class="error">' + message + '</div>',
                    colspan = function(t) {
                        var columns = $(t + '> td'),
                            total = 0;
                        for (var i, len = columns.len, width; i<len; i++) {
                            width = columns[i].attr('colspan');
                            if (width) {
                                total += parseInt(width);
                            } else {
                                total += 1;
                            }
                        }
                        return total;
                    },
                    rowname = function() {
                        if ('none' == rowindex) {
                            return '#add-row-' + formname;
                        } else {
                            return '#edit-row-' + formname;
                        }
                    };
                if (null === fieldname) {
                    // Append error message to the whole subform
                    target = rowname();
                    msg = $('<tr><td colspan="' + colspan(target) + '">' + msg + '</td></tr>');
                } else {
                    // Append error message to subform field
                    target = '#sub_' + formname + '_' + formname + '_i_' + fieldname + '_edit_' + rowindex;
                    if ($(target).is('[type="hidden"]')) {
                        target = rowname();
                        msg = '<tr><td colspan="' + colspan(target) + '">' + msg + '</td></tr>';
                    }
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

            var subForm = $(element).closest('.inline-form');

            subForm.addClass('changed');
            if (subForm.hasClass('add-row')) {
                subForm.find('.inline-dsc').show();
            }
        },

        /**
         * Parse the JSON from the real input, and bind the result
         * as 'data' object to the real input
         *
         * @return {object} the data object
         */
        _deserialize: function() {

            var input = this.input,
                data = JSON.parse(input.val());

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

            var input = this.input,
                json = JSON.stringify(input.data('data'));

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
            addRow.find('.inline-add, .action-lnk').hide();
        },

        /**
         * Enable the add-row
         */
        _enableAddRow: function() {

            var addRow = $('#add-row-' + this.formname);
            addRow.find('input, select, textarea').prop('disabled', false);
            addRow.find('.inline-add, .action-lnk').removeClass('hide').show();
        },

        /**
         * Show or hide non-static header row
         */
        _showHeaders: function() {

            var labelRow = this.labelRow;
            if (labelRow && labelRow.length) {
                var formname = this.formname;
                var visibleReadRows = $('#sub-' + formname + ' .read-row:visible');
                if (visibleReadRows.length) {
                    labelRow.show();
                } else {
                    labelRow.hide();
                }
            }
        },

        /**
         * Ensure that all modifications in inline forms are
         * validated before submission of the main form
         */
        _catchSubmit: function() {

            var form = $(this.element).closest('form'),
                ns = this.eventNamespace + this.id,
                self = this;

            // Get or create map of pending inline-form validations
            var pendingValidations = form.data('pendingValidations');
            if (!pendingValidations) {

                // This is the first inline-form to require validation
                pendingValidations = {};
                form.data('pendingValidations', pendingValidations);

                // Catch submit event
                form.off('submit' + ns).on('submit' + ns, function(event) {

                    // Stop immediate form submission
                    event.preventDefault();

                    // Disable submit button (prevent repeated clicks)
                    form.find('input[type="submit"]').prop('disabled', true);

                    // Trigger inline validation
                    form.trigger('validateInline');

                    // Activate deferred submission
                    self._deferredSubmit(form);
                });
            }

            if (!pendingValidations[ns]) {

                // Report that this inline component needs validation
                pendingValidations[ns] = $.Deferred();

                // Add a handler for the validateInline event
                form.off('validateInline' + ns).on('validateInline' + ns, function() {
                    self._validateAll();
                });
            }
        },

        /**
         * Deferred form submission
         */
        _deferredSubmit: function(form) {

            // Collect all pending validation promises
            var pendingValidations = form.data('pendingValidations'),
                validations = [];
            for (var key in pendingValidations) {
                validations.push(pendingValidations[key]);
            }

            // Submit the form when all inline validations are done
            var ns = this.eventNamespace + this.id;
            $.when.apply(null, validations).then(
                function() {
                    form.off(ns).submit();
                },
                function() {
                    // Validation failed => re-enable submit button
                    form.find('input[type="submit"]').prop('disabled', false);
                });
        },

        // Data Processing and Validation -------------------------------------

        /**
         * Collect the data from the form
         *
         * @param {object} data - the de-serialized JSON data
         * @param {string|integer} rowindex - the index of the input row,
         *                                    usually '0' for the edit-row,
         *                                    and 'none' for the add-row
         * @param {string|integer} editIndex - the index of the edited read-row
         */
        _collectData: function(data, rowindex, editIndex) {

            var formname = this.formname,
                formRow,
                rows = data.data,
                row = {},
                original = null;

            if (rowindex == 'none') {
                formRow = $('#add-row-' + formname);
            } else {
                formRow = $('#edit-row-' + formname);
                var originalIndex = formRow.data('rowindex');
                if (typeof originalIndex != 'undefined') {
                    original = rows[originalIndex];
                }
            }
            if (formRow.length) {
                // Trigger client-side validation:
                // Widgets in this formRow can bind handlers to the validate-event
                // which can stop the data collection (and thus prevent both server-side
                // validation and subform submission) by calling event.preventDefault().
                var event = new $.Event('validate');
                formRow.triggerHandler(event);
                if (event.isDefaultPrevented()) {
                    return null;
                }
            }

            // Retain the original record ID
            if (original !== null) {
                var record_id = original._id;
                if (typeof record_id != 'undefined') {
                    row._id = record_id;
                }
            }

            // Collect the input data
            var fieldname,
                selector,
                input,
                value,
                cssClass,
                intvalue,
                fields = data.fields,
                upload_index;
            for (var i=0; i < fields.length; i++) {

                fieldname = fields[i].name;
                selector = '#sub_' + formname + '_' + formname + '_i_' + fieldname + '_edit_' + rowindex;

                input = $(selector);
                if (input.length) {

                    // Field is Writable
                    value = input.val();

                    if (input.attr('type') == 'file') {

                        // When editing an existing row, upload-fields are empty
                        // unless a new file is uploaded, so if it is not marked
                        // to be deleted, then retain the original file name to
                        // indicate no change (may not pass validation otherwise):
                        if (!value && original) {
                            var dflag = $('#' + formname + '_i_' + fieldname + '_edit_' + rowindex + '__delete');
                            if (!dflag.prop("checked")) {
                                value = original[fieldname].value;
                            }
                        }

                        // Clone the file input ready to accept new files
                        input.clone().insertAfter(input);

                        // Can the sub-form have multiple rows?
                        // => check if Add-button is present
                        var add_button = $('#add-' + formname + '-none'),
                            multiple = !!add_button.length;

                        // Determine the new upload field ID
                        if (!multiple && rowindex == 'none') {
                            // Single row => upload index is always 0
                            upload_index = '0';
                        } else {
                            // Multiple rows => index of the currently edited row,
                            // or the add-row index (='none')
                            upload_index = editIndex || rowindex;
                        }
                        var upload_id = 'upload_' + formname + '_' + fieldname + '_' + upload_index;

                        // Remove any old upload for this index
                        $('#' + upload_id).remove();

                        // Store the original input at the end of the form
                        // - we move the original input as it doesn't contain the file
                        //   otherwise on IE, etc
                        // - see http://stackoverflow.com/questions/415483/clone-a-file-input-element-in-javascript
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
                    } else if (input.hasClass('s3-hierarchy-input')) {
                        if (value) {
                            value = JSON.parse(value);
                        } else {
                            value = null;
                        }
                    } else {
                        cssClass = input.attr('class');
                        if (cssClass == 'generic-widget') {
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
                    if (original !== null) {
                        // Keep current value
                        value = original[fieldname].value;
                    } else if (data.defaults  && (typeof(data.defaults[fieldname]) != 'undefined')) {
                        value = data.defaults[fieldname].value;
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
                        row._error = true;
                    } else {
                        // Delete it
                        row._delete = true;
                    }
                } else {
                    delete row._error;
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
                    delete row._error;
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
                                row._error = true;
                            }
                        } else {
                            // Multiple=false, no other rows can exist => error
                            this._appendError(formname, errorIndex, fieldname, i18n.enter_value);
                            row._error = true;
                        }
                    }
                }
            }

            // Add the defaults
            var defaults = data.defaults;
            for (fieldname in defaults) {
                if (!row.hasOwnProperty(fieldname)) {
                    value = defaults[fieldname].value;
                    row[fieldname] = value;
                }
            }

            // Return the row object
            return row;
        },

        /**
         * Validate a new/updated row (asynchronously)
         *
         * @param {string|number} rowindex - the input row index:
         *                                   - 'none' for add, '0' for edit
         * @param {object} data - the de-serialized JSON data
         * @param {object} row - the new row data
         *
         * @returns: a promise that is resolved (or rejected) when the
         *           validation result has been processed
         */
        _validate: function(data, rowindex, row) {

            var formname = this.formname,
                dfd = $.Deferred();

            if (row._error) {
                // Required row which has already been validated as bad
                this._displayErrors();
                return dfd.reject();
            }

            // Construct the URL
            var c = data.controller,
                f = data['function'],
                resource = data.resource,
                component = data.component,
                url = S3.Ap.concat('/' + c + '/' + f + '/validate.json'),
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
            var rowJSON = JSON.stringify(row),
                self = this;

            $.ajaxS3({
                type: 'POST',
                url: url,
                data: rowJSON,
                dataType: 'json',
                contentType: 'application/json; charset=utf-8',
                // gets moved to .done() inside .ajaxS3
                success: function(response) {

                    // Check and report errors
                    var hasErrors = false;
                    if (!response) {
                        hasErrors = true;
                        self._appendError(formname, rowindex, null, "validation failed");
                    } else if (response.hasOwnProperty('_error')) {
                        hasErrors = true;
                        self._appendError(formname, rowindex, null, response._error);
                    }

                    var item,
                        error;
                    for (var field in response) {
                        item = response[field];
                        if (item.hasOwnProperty('_error')) {
                            error = item._error;
                            if (error == "invalid field") {
                                // Virtual Field - not a real error
                                item.text = item.value;
                            } else {
                                hasErrors = true;
                                self._appendError(formname, rowindex, field, error);
                            }
                        }
                    }

                    if (hasErrors) {
                        self._displayErrors();
                        dfd.reject();
                    } else {
                        // Resolve with validated + represented row
                        dfd.resolve(response);
                    }
                }
            });

            return dfd.promise();
        },

        // Form Actions -------------------------------------------------------

        /**
         * Update an S3UploadWidget (i.e. file-link and image preview) with
         * a new value
         *
         * @param {jQuery} input - the file input element of the upload widget
         * @param {string} value - the file name
         */
        _updateUploadWidget: function(input, value) {

            var pendingUpload = input.val(),
                widget = input.closest('.s3-upload-widget'),
                baseURL = widget.data('base'),
                fileURL;

            if (baseURL) {
                fileURL = baseURL.concat('/', value);
            } else {
                fileURL = S3.Ap.concat('/default/download', value);
            }

            widget.find('.s3-upload-link').each(function() {

                var $this = $(this),
                    anchor = $this.find('a');
                if (value && !pendingUpload) {
                    anchor.attr('href', fileURL);
                    $this.removeClass('hide').show();
                } else {
                    anchor.removeAttr('href');
                    $this.hide();
                }
            });

            var isImage = false;
            if (value) {
                var ext = value.substr(value.lastIndexOf('.') + 1).toLowerCase();
                if (['gif', 'png', 'jpg', 'jpeg', 'bmp'].indexOf(ext) != -1) {
                    isImage = true;
                }
            }
            widget.find('.s3-upload-preview').each(function() {

                var $this = $(this),
                    img = $this.find('img');
                if (isImage && !pendingUpload) {
                    img.attr('src', fileURL);
                    $this.removeClass('hide').show();
                } else {
                    img.attr('src', '');
                    $this.hide();
                }
            });
        },

        /**
         * Edit a row
         *
         * @param {string|number} rowindex - the row index
         *
         * @todo: separate out the update of the read-row
         */
        _editRow: function(rowindex) {

            var formname = this.formname,
                rowname = formname + '-' + rowindex;

            this._removeErrors();

            var data = this._deserialize(),
                fields = data.fields,
                row = data.data[rowindex];

            if (row._readonly) {
                // Can't edit the row if it is read-only
                return;
            }

            // Show all read rows for this field
            $('#sub-' + formname + ' .read-row').removeClass('hide').show();
            // Hide the current read row, unless it's an Image
            if (formname != 'imageimage') {
                $('#read-row-' + rowname).hide();
            }

            // Populate the edit row with the data for this rowindex
            var fieldname,
                element,
                input,
                text,
                value,
                i;

            for (i=0; i < fields.length; i++) {

                fieldname = fields[i].name;
                value = row[fieldname].value;
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
                    this._updateColumn($('#edit-row-' + formname), i, row[fieldname].text);

                } else {

                    if (input.attr('type') == 'file') {

                        // If there is an existing file input for this field+row,
                        // then move it into the edit row in place of the cloned
                        // default input, and update its ID
                        var upload = $('#upload_' + formname + '_' + fieldname + '_' + rowindex);
                        if (upload.length) {
                            var id = input.attr('id');
                            var name = input.attr('name');
                            input.replaceWith(upload);
                            upload.attr('id', id)
                                  .attr('name', name)
                                  .css({display: ''});
                            input = upload;
                        }

                        // Update the upload-widget (i.e. link and image preview)
                        this._updateUploadWidget(input, value);

                        // Also reset the delete-flag in the edit row
                        var dflag = $('#' + formname + '_i_' + fieldname + '_edit_0__delete');
                        dflag.prop("checked", false);

                    } else if (input.attr('type') == 'checkbox') {

                        // Set checked-property from boolean value
                        input.prop('checked', value);

                    } else {

                        // Set input to current value
                        input.val(value);

                        // Refresh widgets
                        if (input.hasClass('multiselect-widget') && input.multiselect('instance')) {
                            input.multiselect('refresh');
                        } else if (input.hasClass('groupedopts-widget') && input.groupedopts('instance')) {
                            input.groupedopts('refresh');
                        } else if (input.hasClass('location-selector') && input.locationselector('instance')) {
                            input.locationselector('refresh');
                        } else if (input.hasClass('s3-hierarchy-input')) {
                            var parent = input.parent();
                            if (parent.hierarchicalopts('instance')) {
                                if (value) {
                                    value = JSON.parse(value);
                                    if (value.constructor !== Array) {
                                        value = [value];
                                    }
                                    parent.hierarchicalopts('set', value);
                                } else {
                                    parent.hierarchicalopts('reset');
                                }
                            }
                        } else if (S3.rtl && input.hasClass('phone-widget')) {
                            if (value && (value.charAt(0) != '\u200E')) {
                                input.val('\u200E' + value);
                            }
                        } else {
                            // Populate text in autocompletes
                            element = '#dummy_sub_' + formname + '_' + formname + '_i_' + fieldname + '_edit_0';
                            text = row[fieldname].text;
                            $(element).val(text);
                        }

                    }
                }
            }

            // Insert the edit row after this read row
            var edit_row = $('#edit-row-' + formname);
            edit_row.insertAfter('#read-row-' + rowname);

            // Remember the current row index in the edit row & show it
            edit_row.data('rowindex', rowindex).removeClass('hide').show();

            // Trigger the dropdown change event
            $('#edit-row-' + formname + ' select:not(".lx-select")').change();

            // Disable the add-row while editing
            this._disableAddRow();
            this._showHeaders();
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
            edit_row.hide()
                    .data('rowindex', null)
                    .removeClass('changed');

            // Show the read-row
            $('#read-row-' + rowname).removeClass('hide').show();

            // Enable the add-row
            this._enableAddRow();
            this._showHeaders();
        },

        /**
         * Reset the add-row to defaults (and hide it if explicitAdd)
         */
        _resetAddRow: function() {

            // formname
            var self = this,
                data = this._deserialize(),
                formName = this.formname,
                formPrefix = 'sub_' + formName + '_' + formName + '_i_';

            // Remove any previous error messages
            this._removeErrors();

            var fields = data.fields,
                fieldName,
                fieldPrefix,
                defaultField,
                defaultValue,
                currentField,
                emptyWidget,
                container;

            // File input change-handler to re-attach after cloning
            var changeHandler = function() {
                self._markChanged(this);
                self._catchSubmit();
            };

            for (var i = fields.length; i--;) {

                fieldName = fields[i].name;
                fieldPrefix = formPrefix + fieldName;

                defaultField = $('#' + fieldPrefix + '_edit_default');
                currentField = $('#' + fieldPrefix + '_edit_none');

                if (currentField.attr('type') == 'file') {

                    // Clone the default file input
                    emptyWidget = defaultField.clone();
                    emptyWidget.attr('id', currentField.attr('id'))
                               .attr('name', currentField.attr('name'))
                               .change(changeHandler);
                    currentField.replaceWith(emptyWidget);

                } else {

                    // Set the input to the default value
                    defaultValue = defaultField.val();
                    currentField.val(defaultValue);

                    // Refresh widgets
                    if (currentField.attr('type') == 'checkbox') {
                        currentField.prop('checked', defaultField.prop('checked'));

                    } else if (currentField.hasClass('multiselect-widget') &&
                               currentField.multiselect('instance')) {
                        currentField.multiselect('refresh');

                    } else if (currentField.hasClass('groupedopts-widget') &&
                               currentField.groupedopts('instance')) {
                        currentField.groupedopts('refresh');

                    } else if (currentField.hasClass('location-selector') &&
                               currentField.locationselector('instance')) {
                        currentField.locationselector('refresh');

                    } else if (currentField.hasClass('s3-hierarchy-input')) {

                        container = currentField.parent();
                        if (container.hierarchicalopts('instance')) {
                            if (defaultValue) {
                                defaultValue = JSON.parse(defaultValue);
                                if (defaultValue.constructor !== Array) {
                                    defaultValue = [defaultValue];
                                }
                                container.hierarchicalopts('set', defaultValue);
                            } else {
                                container.hierarchicalopts('reset');
                            }
                        }
                    }
                }

                // Copy default value for dummy input
                defaultValue = $('#dummy_' + fieldPrefix + '_edit_default').val();
                $('#dummy_' + fieldPrefix + '_edit_none').val(defaultValue);

            }

            var addRow = $('#add-row-' + formName);

            // Unmark changed
            addRow.removeClass('changed');

            var explicitAdd = $(this.element).find('.inline-open-add');
            if (explicitAdd.length) {
                // Hide the add-row if explicit open-action available
                addRow.hide();
                explicitAdd.show();
            } else {
                // Hide the discard-option
                addRow.find('.inline-dsc').hide();
            }
        },

        /**
         * Add a new row
         *
         * @returns {promise} - a promise that resolves when the new row
         *                      has been added successfully
         */
        _addRow: function() {

            var formName = this.formname,
                rowindex = 'none',
                throbber,
                add_button = $('#add-' + formName + '-' + rowindex),
                multiple;

            if (add_button.length) {
                multiple = true;
            } else {
                // Only one row can exist & this must be added during form submission
                multiple = false;
            }

            if (multiple) {
                // Hide add-button, show throbber
                add_button.hide();
                throbber = $('#throbber-' + formName + '-' + rowindex).removeClass('hide').show();

                // Remove any previous error messages
                this._removeErrors();
            }

            // Collect the values from the add-row
            var data = this._deserialize(),
                row_data = this._collectData(data, 'none');
            if (null === row_data) {
                // Data collection failed (e.g. client-side validation error)
                if (multiple) {
                    throbber.hide();
                    add_button.removeClass('hide').show();
                }
                return $.Deferred().reject();
            }

            // If this is an empty required=true row in a multiple=true with existing rows, then don't validate
            var add_required = $('#add-row-' + formName).hasClass('required'),
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
                    if ($('#add-' + formName + '-' + rowindex).length) {
                        // multiple=true, can have other rows
                        if ($('#read-row-' + formName + '-0').length) {
                            // Rows present, so skip validation
                            // Hide throbber, show add-button
                            throbber.hide();
                            add_button.removeClass('hide').show();
                            return $.Deferred().resolve();
                        }
                    }
                }
            }

            // Validate the data
            var validated = this._validate(data, rowindex, row_data),
                self = this;

            return validated.then(
                function(newRow) {

                    if (null !== newRow) {

                        // Mark new row as changed
                        newRow._changed = true;

                        // Add the new row to the real input JSON
                        var newIndex = data.data.push(newRow) - 1;
                        newRow._index = newIndex;
                        self._serialize();

                        if (multiple) {

                            // Create a new read-row, reset the add-row
                            var items = [],
                                fields = data.fields,
                                fieldName,
                                upload,
                                uploadID;

                            for (var i = 0, len = fields.length; i < len; i++) {

                                fieldName = fields[i].name;

                                // Update file input (moved out by _collectData) to the new row index:
                                upload = $('#upload_' + formName + '_' + fieldName + '_none');
                                if (upload.length) {
                                    uploadID = 'upload_' + formName + '_' + fieldName + '_' + newIndex;
                                    $('#' + uploadID).remove();
                                    upload.attr({'id': uploadID, 'name': uploadID});
                                }

                                // Store text representation for the read-row
                                items.push(newRow[fieldName].text);
                            }

                            // Reset add-row to defaults
                            self._resetAddRow();

                            // Render new read row and append to container
                            var readRow = self._renderReadRow(formName, newIndex, items);
                            self._appendReadRow(formName, readRow);

                            // Show table headers
                            // (initially hidden with explicitAdd=true and no rows yet existing)
                            self._showHeaders();
                        }
                    }

                    if (multiple) {
                        // Hide throbber, show add-button
                        throbber.hide();
                        add_button.removeClass('hide').show();
                    }
                },
                function() {
                    // Validation failed
                    if (multiple) {
                        // Hide throbber, show add-button
                        throbber.hide();
                        add_button.removeClass('hide').show();
                    }
                });
        },

        /**
         * Update row
         *
         * @param {string|number} rowindex - the row index
         */
        _updateRow: function(rowindex) {

            var formname = this.formname,
                rdy_button = $('#rdy-' + formname + '-0'),
                multiple,
                throbber;
            if (rdy_button.length) {
                multiple = true;
            } else {
                // Only one row can exist & this must be updated during form submission
                multiple = false;
            }

            if (multiple) {
                // Hide rdy_button, show throbber
                rdy_button.hide();
                throbber = $('#throbber-' + formname + '-0').removeClass('hide').show();

                // Remove any previous error messages
                this._removeErrors();
            }

            // Collect the values from the edit-row
            var data = this._deserialize(),
                row_data = this._collectData(data, '0', rowindex);
            if (null === row_data) {
                // Data collection failed (e.g. client-side validation error)
                if (multiple) {
                    throbber.hide();
                    rdy_button.removeClass('hide').show();
                }
                return $.Deferred().reject();
            }

            if (row_data._delete) {

                // multiple=False form which has set all fields to '' to delete the row
                data.data[rowindex]._delete = true;
                this._serialize();
                return $.Deferred().resolve();

            } else {

                // Validate the form data
                var validated = this._validate(data, '0', row_data),
                    self = this;

                return validated.then(
                    function(new_row) {

                        if (null !== new_row) {

                            // Update the row in the real_input JSON
                            new_row._id = data.data[rowindex]._id;
                            new_row._changed = true; // mark as changed
                            new_row._index = rowindex;
                            data.data[rowindex] = new_row;
                            self._serialize();

                            if (multiple) {
                                // Update read-row in the table, clear edit-row
                                var items = [],
                                    fields = data.fields,
                                    default_value,
                                    i;

                                // File input change-handler to re-attach after cloning
                                var changeHandler = function() {
                                    self._markChanged(self);
                                    self._catchSubmit();
                                };

                                for (i=0; i < fields.length; i++) {
                                    var field = fields[i].name;
                                    items.push(new_row[field].text);

                                    // Reset edit-field to default value
                                    var d = $('#sub_' + formname + '_' + formname + '_i_' + field + '_edit_default'),
                                        f = $('#sub_' + formname + '_' + formname + '_i_' + field + '_edit_0');

                                    if (f.attr('type') == 'file') {

                                        // Clone the default file input
                                        // (because we cannot set the value for file inputs)
                                        var emptyWidget = d.clone();
                                        emptyWidget.attr('id', f.attr('id'))
                                                   .attr('name', f.attr('name'))
                                                   .change(changeHandler);
                                        f.replaceWith(emptyWidget);

                                    } else {

                                        // Set input to default value
                                        default_value = d.val();
                                        f.val(default_value);

                                        // @todo: shouldn't we update widgets here too?
                                    }

                                    // Copy default value for dummy input
                                    default_value = $('#dummy_sub_' + formname + '_' + formname + '_i_' + field + '_edit_default').val();
                                    $('#dummy_sub_' + formname + '_' + formname + '_i_' + field + '_edit_0').val(default_value);
                                }
                                // Unmark changed
                                var edit_row = $('#edit-row-' + formname);
                                edit_row.removeClass('changed');

                                // Update the read row
                                var read_row = self._renderReadRow(formname, rowindex, items);

                                // Hide and reset the edit row rowindex
                                edit_row.hide().data('rowindex', null);

                                // Show the read row
                                read_row.removeClass('hide').show();

                                // Re-enable add-row
                                self._enableAddRow();
                                self._showHeaders();
                            }
                        }

                        if (multiple) {
                            // Hide throbber, enable rdy_button
                            throbber.hide();
                            rdy_button.removeClass('hide').show();
                        }
                    },
                    function() {
                        // Validation failed
                        if (multiple) {
                            // Hide throbber, enable rdy_button
                            throbber.hide();
                            rdy_button.removeClass('hide').show();
                        }
                    });
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
            data.data[rowindex]._delete = true;
            this._serialize();

            // Remove the read-row for this item
            $('#read-row-' + rowname).remove();
            this._showHeaders();

            // Remove all uploads for this item
            $('input[name^="' + 'upload_' + formname + '_"][name$="_' + rowindex + '"]').remove();

            var edit_row = $('#edit-row-' + formname);
            if (edit_row.hasClass('required')) {
                if (!$('#read-row-' + formname + '-0').length) {
                    // No more rows present - set the add row as required
                    $('#add-row-' + formname).addClass('required');
                    edit_row.removeClass('required');
                    // Ensure we validate this if not changed
                    this._catchSubmit();
                }
            }

            return true;
        },

        // Event Handlers -----------------------------------------------------

        /**
         * Validate all pending changes in this inline form
         */
        _validateAll: function() {

            var self = this,
                validations = [];

            // Find and validate all pending rows
            $(self.element).find('.inline-form.changed, .inline-form.required')
                           .each(function() {

                var row = $(this),
                    empty = true;

                if (row.hasClass('required')) {
                    // Treat required rows as non-empty
                    empty = false;

                } else {
                    // Check that the row contains data
                    var inputs = row.find('input, select, textarea'),
                        input,
                        tokens,
                        defaultInput;

                    for (var i = inputs.length; i--;) {

                        input = $(inputs[i]);

                        // Ignore hidden inputs unless they have an 'input' flag
                        if (input.is('[type="hidden"]')) {
                            if (!input.data('input')) {
                                continue;
                            }
                        } else if (!input.is(':visible')) {
                            continue;
                        }

                        // Treat SELECTs as empty if only the default value is selected
                        // ...except in single-rows => always create what is visible
                        if (input.prop('tagName') == 'SELECT' && !row.hasClass('single')) {
                            tokens = input.attr('id').split('_');
                            tokens.pop();
                            tokens.push('default');
                            defaultInput = $('#' + tokens.join('_'));
                            if (defaultInput.length && defaultInput.val() == input.val()) {
                                continue;
                            }
                        }

                        if ((input.attr('type') != 'checkbox' && input.val()) || input.prop('checked')) {
                            empty = false;
                            break;
                        }
                    }
                }

                // If not empty, process it
                if (!empty) {
                    if (row.hasClass('add-row')) {
                        validations.push(self._addRow());
                    } else {
                        validations.push(self._updateRow(row.data('rowindex')));
                    }
                }
            });

            var form = $(this.element).closest('form'),
                pendingValidations = form.data('pendingValidations'),
                ns = this.eventNamespace + this.id;

            $.when.apply(null, validations).then(
                function() {
                    // This inline-component is valid
                    if (pendingValidations[ns]) {
                        // Resolve + remove the validation promise
                        // (subsequent changes will create a new one)
                        pendingValidations[ns].resolve();
                        delete pendingValidations[ns];
                    }
                    // Remove validateInline handler
                    // (will be re-added if changed again)
                    form.off('validateInline' + ns);
                },
                function() {
                    // This inline-component is not valid
                    if (pendingValidations[ns]) {
                        // Reject the validation promise, and create a
                        // new one; leave the validateInline handler in
                        // place so this component is re-validated when
                        // Submit is clicked again
                        pendingValidations[ns].reject();
                        pendingValidations[ns] = $.Deferred();
                    }
                });
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
                data = self._deserialize().data;

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
                if (item.hasOwnProperty('_delete')) {
                    delete item._delete;
                }
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
                ns = this.eventNamespace,
                self = this;

            // Button events
            el.on('click' + ns, '.read-row', function(e) {
                // Click into read-row opens the row for edit
                // (unless the click-target is a link anchor)
                var target = e.target;
                if (!target || target.tagName != "A" || !target.href) {
                    var names = $(this).attr('id').split('-'),
                        rowindex = names.pop();
                    e.preventDefault();
                    self._editRow(rowindex);
                    return false;
                }
            }).on('click' + ns, '.inline-add', function() {
                self._addRow();
                return false;
            }).on('click' + ns, '.inline-dsc', function() {
                self._resetAddRow();
                return false;
            }).on('click' + ns, '.inline-cnc', function() {
                var names = $(this).attr('id').split('-');
                names.pop();
                var formname = names.pop(),
                    rowindex = $('#edit-row-' + formname).data('rowindex');
                self._cancelEdit(rowindex);
                return false;
            }).on('click' + ns, '.inline-rdy', function() {
                var names = $(this).attr('id').split('-');
                names.pop();
                var formname = names.pop(),
                    rowindex = $('#edit-row-' + formname).data('rowindex');
                self._updateRow(rowindex);
                return false;
            }).on('click' + ns, '.inline-edt', function() {
                var names = $(this).attr('id').split('-'),
                    rowindex = names.pop();
                self._editRow(rowindex);
                return false;
            }).on('click' + ns, '.inline-rmv', function() {
                var names = $(this).attr('id').split('-'),
                    rowindex = names.pop();
                self._removeRow(rowindex);
                return false;
            }).on('click' + ns, '.error', function() {
                $(this).fadeOut('medium', function() { $(this).remove(); });
                return false;
            });

            // Form events
            var inputs = 'input',
                textInputs = 'input[type="text"],input[type="file"],textarea',
                fileInputs = 'input[type="file"]',
                dateInputs = 'input.s3-calendar-widget',
                otherInputs = 'input[type!="text"][type!="file"],select',
                multiSelects = 'select.multiselect-widget',
                hierarchyInputs = 'input.s3-hierarchy-input';

            el.find('.add-row,.edit-row').each(function() {
                var $this = $(this);
                // Event to be triggered to force recollection of data (used by LocationSelector when modifying Point/Polygon on map)
                $this.find('div.map_wrapper').on('change' + ns, function() {
                    self._markChanged(this);
                    self._catchSubmit();
                });

                $this.find(textInputs).on('input' + ns, function() {
                    self._markChanged(this);
                    self._catchSubmit();
                });
                $this.find(fileInputs).on('change' + ns, function() {
                    self._markChanged(this);
                    self._catchSubmit();
                });
                $this.find(dateInputs).on('change' + ns, function() {
                    self._markChanged(this);
                    self._catchSubmit();
                });
                $this.find(otherInputs).on('focusin' + ns, function() {
                    $(this).one('change' + ns, function() {
                        self._markChanged(this);
                        self._catchSubmit();
                    }).one('focusout', function() {
                        $(this).off('change' + ns);
                    });
                });
                $this.find(multiSelects).on('multiselectopen' + ns, function() {
                    $(this).off('change' + ns)
                           .one('change' + ns, function() {
                        self._markChanged(this);
                        self._catchSubmit();
                    });
                });
                $this.find(hierarchyInputs).on('change' + ns, function() {
                    self._markChanged(this);
                    self._catchSubmit();
                });
                $this.find(inputs).on('keypress' + ns, function(e) {
                    if (e.which == 13) {
                        e.preventDefault();
                        return false;
                    }
                    return true;
                });
            });

            el.find('.add-row').each(function() {
                $(this).find(inputs).on('keyup' + ns, function(e) {
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
                $(this).find(inputs).on('keyup' + ns, function(e) {
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
                el.on('click' + ns, ':checkbox', {widget: this}, this._checkboxOnClick);
            }

            // Event Management for S3SQLInlineComponentMultiSelectWidget
            if (el.hasClass('inline-multiselect')) {
                el.find('.inline-multiselect-widget')
                  .on('change' + ns, {widget: this}, this._multiselectOnChange);
            }

            // Explicit open-action to reveal the add-row
            el.find('.inline-open-add').on('click' + ns, function(e) {
                e.preventDefault();
                $('#add-row-' + self.formname).removeClass('hide').show();
                $(this).hide();
            });

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var el = $(this.element),
                ns = this.eventNamespace;

            // Remove inline-multiselect-widget event handlers
            if (el.hasClass('inline-multiselect')) {
                el.find('.inline-multiselect-widget').off(ns);
            }

            // Remove inline-locationselector-widget event handlers
            el.find('.inline-locationselector-widget').off(ns);

            // Remove all form event handlers
            el.find('.add-row,.edit-row').each(function() {
                $(this).find('input,textarea,select').off(ns);
            });

            // Remove open-action event handler
            el.find('.inline-open-add').off(ns);

            // Remove all delegations
            el.off(ns);

            return true;
        }
    });
})(jQuery);

$(document).ready(function() {
    // Activate on all inline-components in the current page
    $('.inline-component').inlinecomponent({});
});
