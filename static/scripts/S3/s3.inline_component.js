/**
 * Used by S3SQLInlineComponent & sub-Classes (modules/s3forms.py)
 */

$(function() {

    var inline_current_formname = 'none';
    var inline_current_rowindex = 'none';

    // Utilities --------------------------------------------------------------

    // Mark an inline row as changed
    var inline_mark_changed = function(element) {
        var subform = $(element).closest('tr.inline-form');
        $(subform).addClass('changed');
    };

    // Get the real input name
    var inline_get_field = function(formname) {
        var selector = '#sub-' + formname;
        var field = $(selector).attr('field');
        return field;
    };

    // Read JSON from real_input, decode and store as data object
    var inline_deserialize = function(formname) {
        var selector = inline_get_field(formname);
        var real_input = $('#' + selector);
        var data_json = real_input.val();
        var data = JSON.parse(data_json);
        real_input.data('data', data);
        return data;
    };

    // Serialize the data object as JSON and store into real_input
    var inline_serialize = function(formname) {
        var selector = inline_get_field(formname);
        var real_input = $('#' + selector);
        var data = real_input.data('data');
        var data_json = JSON.stringify(data);
        real_input.val(data_json);
        return data_json;
    };

    // Append an error to a form field or row
    var inline_append_error = function(formname, rowindex, fieldname, message) {
        var field_id, msg;
        if (null === fieldname) {
            if ('none' == rowindex) {
                field_id = '#add-row-' + formname;
            } else {
                field_id = '#edit-row-' + formname;
            }
            var l = $(field_id + '> td').length;
            msg = '<tr class="' + formname + '_error">' +
                    '<td colspan="' + l + '">' +
                      '<div class="error">' +
                        message +
                      '</div></td></tr>';
        } else {
            field_id = '#sub_' + formname + '_' + formname + '_i_' + fieldname + '_edit_' + rowindex;
            msg = '<div class="' + formname + '_error error">' + message + '</div>';
        }
        $(field_id).after(msg);
        $('.' + formname + '_error').hide();
        $('.error').click(function() {
            $(this).fadeOut('slow');
            return false;
        });
    };

    // Display all errors
    var inline_display_errors = function(formname) {
        $('.' + formname + '_error').show();
    };

    // Remove all error messages from the form
    var inline_remove_errors = function(formname) {
        $('.' + formname + '_error').remove();
    };

    // Disable the add-row
    var disable_inline_add = function(formname) {
        var add_tds = $('#add-row-' + formname + ' > td');
        add_tds.find('input, select, textarea').prop('disabled', true);
        add_tds.find('.inline-add, .action-lnk').addClass('hide');
    };

    // Enable the add-row
    var enable_inline_add = function(formname) {
        var add_tds = $('#add-row-' + formname + ' > td');
        add_tds.find('input, select, textarea').prop('disabled', false);
        add_tds.find('.inline-add, .action-lnk').removeClass('hide');
    };

    // Collect the data from the form
    var inline_collect_data = function(formname, data, rowindex) {

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
            fields = data['fields'];
        for (var i=0; i < fields.length; i++) {
            fieldname = fields[i]['name'];
            selector = '#sub_' +
                       formname + '_' + formname + '_i_' +
                       fieldname + '_edit_' + rowindex;
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
                    var add_button = $('#add-' + formname + '-' + rowindex);
                    if (add_button.length) {
                        var multiple = true;
                    } else {
                        // Only one row can exist & this must be added during form submission
                        var multiple = false;
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
            // setting all fields to '' => delete
            var del = true;
            for (fieldname in row) {
                if ((fieldname != '_id') && (row[fieldname] != '')) {
                    del = false;
                }
            }
            if (del) {
                var required = $('#edit-row-' + formname).hasClass('required');
                if (required) {
                    // Cannot delete
                    inline_append_error(formname, rowindex, fieldname, i18n.enter_value);
                    row['_error'] = true;
                } else {
                    // Delete
                    row['_delete'] = true;
                }
            } else {
                delete row['_error'];
            }
        } else {
            // Check if subform is required
            var add_required = $('#add-row-' + formname).hasClass('required');
            if (add_required) {
                delete row['_error'];
                var empty = true;
                for (fieldname in row) {
                    if ((fieldname != '_id') && (row[fieldname] != '')) {
                        empty = false;
                    }
                }
                if (empty) {
                    // Check if we have other rows
                    if ($('#add-' + formname + '-' + rowindex).length) {
                        // multiple=true, can have other rows
                        if (!$('#read-row-' + formname + '-0').length) {
                            // No rows present
                            inline_append_error(formname, rowindex, fieldname, i18n.enter_value);
                            row['_error'] = true;
                        }
                    } else {
                        // multiple=false, no other rows
                        inline_append_error(formname, rowindex, fieldname, i18n.enter_value);
                        row['_error'] = true;
                    }
                }
            } else {
                var edit_required = $('#edit-row-' + formname).hasClass('required');
                if (edit_required) {
                    delete row['_error'];
                    var empty = true;
                    for (fieldname in row) {
                        if ((fieldname != '_id') && (row[fieldname] != '')) {
                            empty = false;
                        }
                    }
                    if (empty) {
                        // Check if we have other rows
                        if ($('#add-' + formname + '-' + rowindex).length) {
                            // multiple=true, can have other rows
                            if (!$('#read-row-' + formname + '-0').length) {
                                // No rows present
                                inline_append_error(formname, rowindex, fieldname, i18n.enter_value);
                                row['_error'] = true;
                            }
                        } else {
                            // multiple=false, no other rows
                            inline_append_error(formname, rowindex, fieldname, i18n.enter_value);
                            row['_error'] = true;
                        }
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
    };

    // Validate a new/updated row
    var inline_validate = function(formname, rowindex, data, row) {

        if (row['_error']) {
            // Required row which has already been validated as bad
            inline_display_errors(formname);
            return null;
        }

        // Construct the URL
        var c = data['controller'];
        var f = data['function'];
        var url = S3.Ap.concat('/' + c + '/' + f + '/validate.json');
        var resource = data['resource'];
        if (null !== resource && typeof resource != 'undefined') {
            url += '?resource=' + resource;
            concat = '&';
        } else {
            concat = '?';
        }
        var component = data['component'];
        if (null !== component && typeof component != 'undefined') {
            url += concat + 'component=' + component;
        }

        // Request validation of the row
        // @ToDo: Skip read-only fields (especially Virtual)
        var row_json = JSON.stringify(row);
        var response = null;
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
            has_errors = true
        } else if (response.hasOwnProperty('_error')) {
            has_errors = true;
            inline_append_error(formname, rowindex, null, response['_error']);
        }
        var item,
            error;
        for (field in response) {
            item = response[field];
            if (item.hasOwnProperty('_error')) {
                error = item['_error'];
                if (error == "invalid field") {
                    // Virtual Field - not a real error
                    item['text'] = item['value'];
                } else {
                    inline_append_error(formname, rowindex, field, error);
                    has_errors = true;
                }
            }
        }

        // Return the validated + represented row
        // (or null if there was an error)
        if (has_errors) {
            inline_display_errors(formname);
            return null;
        } else {
            return response;
        }
    };

    // Form actions -----------------------------------------------------------

    // Edit a row
    var inline_edit = function(formname, rowindex) {
        var rowname = formname + '-' + rowindex;

        inline_remove_errors(formname);

        // Show all read rows for this field
        $('#sub-' + formname + ' .read-row').removeClass('hide');
        // Hide the current read row, unless it's an Image
        if (formname != 'imageimage') {
            $('#read-row-' + rowname).addClass('hide');
        };

        // Populate the edit row with the data for this rowindex
        var data = inline_deserialize(formname);
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
                text = row[fieldname]['text'];
                var td = $('#edit-row-' + formname + ' td')[i];
                td.innerHTML = text;
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
                    if (input.hasClass('multiselect-widget')) {
                        input.multiselect('refresh');
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
        $('#edit-row-' + formname + ' select').change();

        // Disable the add-row while editing
        disable_inline_add(formname);
    };

    // Cancel editing a row
    var inline_cancel = function(formname, rowindex) {
        var rowname = formname + '-' + rowindex;

        inline_remove_errors(formname);

        var edit_row = $('#edit-row-' + formname);
        
        // Hide and reset the edit-row
        edit_row.addClass('hide')
                .data('rowindex', null)
                .removeClass('changed');
        
        // Show the read-row
        $('#read-row-' + rowname).removeClass('hide');

        // Enable the add-row
        enable_inline_add(formname);
    };

    // Add a new row
    var inline_add = function(formname) {
        var rowindex = 'none';

        var add_button = $('#add-' + formname + '-' + rowindex);
        if (add_button.length) {
            var multiple = true;
        } else {
            // Only one row can exist & this must be added during form submission
            var multiple = false;
        }

        if (multiple) {
            // Hide add-button, show throbber
            add_button.addClass('hide');
            var throbber = $('#throbber-' + formname + '-' + rowindex);
            throbber.removeClass('hide');

            // Remove any previous error messages
            inline_remove_errors(formname);
        }

        // Collect the values from the add-row
        var data = inline_deserialize(formname);
        var row_data = inline_collect_data(formname, data, 'none');

        // If this is an empty required=true row in a multiple=true with existing rows, then don't validate
        var add_required = $('#add-row-' + formname).hasClass('required');
        if (add_required) {
            var empty = true;
            for (fieldname in row_data) {
                if ((fieldname != '_id') && (row_data[fieldname] != '')) {
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
        var new_row = inline_validate(formname, rowindex, data, row_data);

        var success = false;
        if (null !== new_row) {
            success = true;
            // Add a new row to the real_input JSON
            new_row['_changed'] = true; // mark as changed
            var newindex = data['data'].push(new_row) - 1;
            new_row['_index'] = newindex;
            inline_serialize(formname, data);

            if (multiple) {
                // Create a new read-row, clear add-row
                var read_row = '<tr id="read-row-' + formname + '-' + newindex + '" class="read-row">';
                var fields = data['fields'];
                var i, field, upload, d, f, default_value;
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
                    read_row += '<td>' + new_row[field]['text'] + '</td>';
                    // Reset add-field to default value
                    d = $('#sub_' + formname + '_' + formname + '_i_' + field + '_edit_default');
                    f = $('#sub_' + formname + '_' + formname + '_i_' + field + '_edit_none');
                    if (f.attr('type') == 'file') {
                        var empty = d.clone();
                        empty.attr('id', f.attr('id'))
                             .attr('name', f.attr('name'))
                             // Set event onto new input to Mark row changed when new files uploaded
                             .change(function() {
                            inline_mark_changed(this);
                            inline_catch_submit(this);
                        });
                        f.replaceWith(empty);
                    } else {
                        default_value = d.val();
                        f.val(default_value);
                        if (f.attr('type') == 'checkbox') {
                            f.prop('checked', d.prop('checked'));
                        }
                    }
                    default_value = $('#dummy_sub_' + formname + '_' + formname + '_i_' + field + '_edit_default').val();
                    $('#dummy_sub_' + formname + '_' + formname + '_i_' + field + '_edit_none').val(default_value);
                }
                // Unmark changed
                $('#add-row-' + formname).removeClass('changed');
                
                // Add edit-button
                if ($('#edt-' + formname + '-none').length !== 0) {
                    read_row += '<td><div><div id="edt-' + formname + '-' + newindex + '" class="inline-edt"></div></div></td>';
                } else {
                    read_row += '<td></td>';
                }
                // Add remove-button
                if ($('#rmv-' + formname + '-none').length !== 0) {
                    read_row += '<td><div><div id="rmv-' + formname + '-' + newindex + '" class="inline-rmv"></div></div></td>';
                } else {
                    read_row += '<td></td>';
                }
                read_row += '</tr>';
                // Append the new read-row to the table
                $('#sub-' + formname + ' > table.embeddedComponent > tbody').append(read_row);
                inline_button_events();
            }
        }

        if (multiple) {
            // Hide throbber, show add-button
            throbber.addClass('hide');
            add_button.removeClass('hide');
        }

        return success;
    };

    // Update row
    var inline_update = function(formname, rowindex) {
        var rowname = formname + '-' + rowindex;

        var rdy = $('#rdy-' + formname + '-0');
        if (rdy.length) {
            var multiple = true;
        } else {
            // Only one row can exist & this must be updated during form submission
            var multiple = false;
        }

        if (multiple) {
            // Hide rdy, show throbber
            rdy.addClass('hide');
            var throbber = $('#throbber-' + formname + '-0');
            throbber.removeClass('hide');

            // Remove any previous error messages
            inline_remove_errors(formname);
        }

        // Collect the values from the edit-row
        var data = inline_deserialize(formname);
        var row_data = inline_collect_data(formname, data, '0');

        if (row_data['_delete']) {

            // multiple=False form which has set all fields to '' to delete the row
            data['data'][rowindex]['_delete'] = true;
            inline_serialize(formname, data);
            return true;

        } else {
            // Validate the form data
            var new_row = inline_validate(formname, rowindex, data, row_data);

            var success = false;
            if (null !== new_row) {
                success = true;

                // Update the row in the real_input JSON
                new_row['_id'] = data['data'][rowindex]['_id'];
                new_row['_changed'] = true; // mark as changed
                new_row['_index'] = rowindex;
                data['data'][rowindex] = new_row;
                inline_serialize(formname, data);

                if (multiple) {
                    // Update read-row in the table, clear edit-row
                    var read_row = '',
                        fields = data['fields'],
                        default_value,
                        i;
                    for (i=0; i < fields.length; i++) {
                        var field = fields[i]['name'];
                        read_row += '<td>' + new_row[field]['text'] + '</td>';
                        // Reset edit-field to default value
                        var d = $('#sub_' + formname + '_' + formname + '_i_' + field + '_edit_default');
                        var f = $('#sub_' + formname + '_' + formname + '_i_' + field + '_edit_0');
                        if (f.attr('type') == 'file') {
                            var empty = d.clone();
                            empty.attr('id', f.attr('id'))
                                 .attr('name', f.attr('name'))
                                 // Set event onto new input to Mark row changed when new files uploaded
                                 .change(function() {
                                inline_mark_changed(this);
                                inline_catch_submit(this);
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
                    
                    // Add edit-button
                    if ($('#edt-' + formname + '-none').length !== 0) {
                        read_row += '<td><div><div id="edt-' + formname + '-' + rowindex + '" class="inline-edt"></div></div></td>';
                    } else {
                        read_row += '<td></td>';
                    }
                    // Add remove-button
                    if ($('#rmv-' + formname + '-none').length !== 0) {
                        read_row += '<td><div><div id="rmv-' + formname + '-' + rowindex + '" class="inline-rmv"></div></div></td>';
                    } else {
                        read_row += '<td></td>';
                    }

                    $('#read-row-' + formname + '-' + rowindex + ' > td').remove();
                    $('#read-row-' + formname + '-' + rowindex).html(read_row);
                    inline_button_events();

                    // Hide and reset the edit row
                    edit_row.addClass('hide')
                            // Reset rowindex
                            .data('rowindex', null);

                    // Show the read row
                    $('#read-row-' + rowname).removeClass('hide');

                    // Re-enable add-row
                    enable_inline_add(formname);
                }
            }

            if (multiple) {
                // Hide throbber, enable rdy
                rdy.removeClass('hide');
                throbber.addClass('hide');
            }

            return (success);
        }
    };

    // Remove a row
    var inline_remove = function(formname, rowindex) {
        var rowname = formname + '-' + rowindex;

        // Confirmation dialog
        if (!confirm(i18n.delete_confirmation)) {
            return false;
        }

        // Update the real_input JSON with deletion of this row
        var data = inline_deserialize(formname);
        data['data'][rowindex]['_delete'] = true;
        inline_serialize(formname, data);

        // Remove the read-row for this item
        $('#read-row-' + rowname).remove();

        // Remove all uploads for this item
        $('input[name^="' + 'upload_' + formname + '_"][name$="_' + rowindex + '"]').remove();

        var edit_row = $('#edit-row-' + formname);
        if (edit_row.hasClass('required')) {
            if (!$('#read-row-' + formname + '-0').length) {
                // No more rows present - set the add row as required
                $('#add-row-' + formname).addClass('required')
                edit_row.removeClass('required')
                // Ensure we validate this if not changed
                inline_catch_submit(edit_row);
            }
        }

        return true;
    };

    // Event handlers ---------------------------------------------------------

    // Submit all changed inline-rows, and then the main form
    var inline_submit_all = function(event) {
        event.preventDefault();
        var $form = $(this),
            _success,
            success = true;

        var changed = $form.find('tr.inline-form.changed, tr.inline-form.required');
        if (changed.length) {
            changed.each(function() {
                var $this = $(this);
                var formname = $this.attr('id').split('-').pop();
                if ($this.hasClass('add-row')) {
                    _success = inline_add(formname);
                } else {
                    var rowindex = $this.data('rowindex');
                    _success = inline_update(formname, rowindex);
                }
                if (!_success) {
                    success = false;
                }
            });
        }

        if (success) {
            $('form').unbind('submit', inline_submit_all);
            $form.submit();
        }
    }

    // Ensure that all inline forms are checked upon submission of main form
    var inline_catch_submit = function(element) {
        $(element).closest('form').unbind('submit', inline_submit_all)
                                  .bind('submit', inline_submit_all);
    }

    // Events -----------------------------------------------------------------

    var inline_form_events = function() {

        // Change-events
        $('.edit-row input[type="text"], .edit-row textarea').bind('input', function() {
            inline_mark_changed(this);
            inline_catch_submit(this);
        });
        $('.edit-row input[type!="text"], .edit-row select').bind('focusin', function() {
            $('.edit-row input[type!="text"], .edit-row select').one('change', function() {
                inline_mark_changed(this);
                inline_catch_submit(this);
            });
        });
        $('.edit-row select.multiselect-widget').bind('multiselectopen', function() {
            $('.edit-row select.multiselect-widget').one('change', function() {
                inline_mark_changed(this);
                inline_catch_submit(this);
            });
        });
        $('.add-row input[type="text"], .add-row textarea').bind('input', function() {
            inline_mark_changed(this);
            inline_catch_submit(this);
        });
        $('.add-row input[type!="text"], .add-row select').bind('focusin', function() {
            $('.add-row input[type!="text"], .add-row select').one('change', function() {
                inline_mark_changed(this);
                inline_catch_submit(this);
            });
        });
        $('.add-row select.multiselect-widget').bind('multiselectopen', function() {
            $('.add-row select.multiselect-widget').one('change', function() {
                inline_mark_changed(this);
                inline_catch_submit(this);
            });
        });
        // Chrome doesn't mark row as changed when just file input added
        $('.add-row input[type="file"]').change(function() {
            inline_mark_changed(this);
            inline_catch_submit(this);
        });

        // Submit the inline-row instead of the main form if pressing Enter
        $('.edit-row input').keypress(function(e) {
            if (e.which == 13) {
                e.preventDefault();
                return false;
            }
            return true;
        }).keyup(function(e) {
            if (e.which == 13) {
                var subform = $(this).parent().parent();
                var names = subform.attr('id').split('-');
                inline_update(names.pop(), subform.data('rowindex'));
            }
        });
        $('.add-row input').keypress(function(e) {
            if (e.which == 13) {
                e.preventDefault();
                return false;
            }
            return true;
        }).keyup(function(e) {
            if (e.which == 13) {
                var subform = $(this).parent().parent();
                var names = subform.attr('id').split('-');
                inline_add(names.pop());
            }
        });
    };

    var inline_button_events = function() {

        $('.inline-add').unbind('click')
                        .click(function() {
            var names = $(this).attr('id').split('-');
            var rowindex = names.pop();
            var formname = names.pop();
            inline_add(formname);
            return false;
        });
        $('.inline-cnc').unbind('click')
                        .click(function() {
            var names = $(this).attr('id').split('-');
            var zero = names.pop();
            var formname = names.pop();
            var rowindex = $('#edit-row-' + formname).data('rowindex');
            inline_cancel(formname, rowindex);
            return false;
        });
        $('.inline-rdy').unbind('click')
                        .click(function() {
            var names = $(this).attr('id').split('-');
            var zero = names.pop();
            var formname = names.pop();
            var rowindex = $('#edit-row-' + formname).data('rowindex');
            inline_update(formname, rowindex);
            return false;
        });
        $('.inline-edt').unbind('click')
                        .click(function() {
            var names = $(this).attr('id').split('-');
            var rowindex = names.pop();
            var formname = names.pop();
            inline_edit(formname, rowindex);
            return false;
        });
        $('.inline-rmv').unbind('click')
                        .click(function() {
            var names = $(this).attr('id').split('-');
            var rowindex = names.pop();
            var formname = names.pop();
            inline_remove(formname, rowindex);
            return false;
        });
    };

    var inline_checkbox_events = function() {
        // Listen for changes on all Inline Checkboxes
        $('.inline-checkbox :checkbox').click(function() {
            var $this = $(this);
            var value = $this.val();
            var names = $this.attr('id').split('-');
            var formname = names[1];
            var fieldname = names[2];
            // Read current data from real input
            var data = inline_deserialize(formname);
            var _data = data['data'];
            var i, item;
            for (var prop in _data) {
                i = _data[prop];
                if (i.hasOwnProperty(fieldname) && i[fieldname]['value'] == value) {
                    item = i;
                    break;
                }
            }
            // Modify data
            if ($this.prop('checked')) {
                if (!item) {
                    // Not yet found, so initialise
                    var label = $this.next().html(); // May be fragile to different formstyles :/
                    item = {};
                    item[fieldname] = {'text': label, 'value': value};
                    _data.push(item);
                }
                item['_changed'] = true;
            } else if (item && item.hasOwnProperty('_id')) {
                item['_delete'] = true;
            }
            // Write data back to real input
            inline_serialize(formname);
        });
    };

    // Make global for OptionsFilter script
    S3.inline_checkbox_events = inline_checkbox_events;

    // Used by S3SQLInlineComponentMultiSelectWidget
    var inline_multiselect_events = function() {
        // Listen for changes on all Inline MultiSelect Widgets
        $('.inline-multiselect-widget').change(function() {
            var $this = $(this);
            var values = $this.val();
            var names = $this.attr('id').split('-');
            var formname = names[0];
            var fieldname = names[1];
            // Read current data from real input
            var data = inline_deserialize(formname);
            var _data = data['data'];
            var old_values = [];
            var i;
            for (var prop in _data) {
                i = _data[prop];
                if (i.hasOwnProperty(fieldname)) {
                    old_values.push(i[fieldname]['value'].toString());
                }
            }
            // Modify the Data
            var new_items = $(values).not(old_values).get();
            var item,
                value,
                len = new_items.length;
            if (len) {
                var label;
                for (i = 0; i < len; i++) {
                    item = {};
                    value = new_items[i];
                    label = $this.find('option[value=' + value + ']').html();
                    item[fieldname] = {'text': label,
                                       'value': value
                                       };
                    item['_changed'] = true;
                    _data.push(item);
                }
            }
            var old_items = $(old_values).not(values).get();
            len = old_items.length;
            if (len) {
                for (i = 0; i < len; i++) {
                    value = old_items[i];
                    for (var prop in _data) {
                        item = _data[prop];
                        if ((item.hasOwnProperty(fieldname)) && (item[fieldname]['value'] == value)) {
                            item['_delete'] = true;
                        }
                    }
                }
            }
            // Write data back to real input
            inline_serialize(formname);
        });
    };

    // Used by S3LocationSelectorWidget2
    var inline_locationselector_events = function() {
        // Listen for changes on all Inline S3LocationSelectorWidget2s
        $('.inline-locationselector-widget').change(function() {
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
            var data = inline_deserialize(formname);
            var _data = data['data'],
                new_value = $this.val(),
                old_value,
                item,
                found = false;
            for (var prop in _data) {
                item = _data[prop];
                if (item.hasOwnProperty(fieldname)) {
                    found = true;
                    old_value = item[fieldname].value;
                    if (old_value) {
                        old_value = old_value.toString();
                    }
                    break;
                }
            }
            if (found && (new_value != old_value)) {
                // Modify the Data
                item[fieldname].value = new_value;
                var represent = 'todo'; // Calculate represent from Street Address or lowest-Lx. Only needed when we support multiple=True
                item[fieldname].text = represent;
                item['_changed'] = true;
            } else if (new_value) {
                // Add a New Item
                var item = {};
                var represent = 'todo';
                item[fieldname] = {'text': represent,
                                   'value': new_value
                                   };
                item['_changed'] = true;
                _data.push(item);
            }
            // Write data back to real input
            inline_serialize(formname);
        });
    };

    $(document).ready(function() {
        if ($('.error_wrapper').length) {
            // Used by S3SQLInlineComponentCheckbox
            // Errors in form, so ensure we show correct checkbox status
            var checkboxes = $('.inline-checkbox :checkbox');
            var checkbox, value, names, formname, fieldname, data, _data, item, i;
            for (var c=0; c < checkboxes.length; c++) {
                checkbox = $(checkboxes[c]);
                value = checkbox.val();
                names = checkbox.attr('id').split('-');
                formname = names[1];
                fieldname = names[2];
                // Read current data from real input
                data = inline_deserialize(formname);
                _data = data['data'];
                item = 0;
                for (var prop in _data) {
                    i = _data[prop];
                    if (i.hasOwnProperty(fieldname) && i[fieldname]['value'] == value) {
                        item = i;
                        break;
                    }
                }
                // Modify checkbox state, as-required
                if (item) {
                    if (item['_changed']) {
                        checkbox.prop('checked', true);
                    } else if (item['_delete']) {
                        checkbox.prop('checked', false);
                    }
                }
            }
        }

        // Check for multiple=False subforms
        $('.inline-form.read-row.single').each(function() {
            // Open Edit Row by default
            var names = $(this).attr('id').split('-');
            var rowindex = names.pop(); // Will always be 0
            var formname = names.pop();
            inline_edit(formname, rowindex);
        });
        $('.inline-form.add-row.single').each(function() {
            var defaults = false;
            $(this).find('input, select').each(function() {
                if ($(this).val()) {
                    defaults = true;
                }
            });
            if (defaults) {
                // Ensure these get validated whether or not they are changed
                inline_mark_changed(this);
                inline_catch_submit(this);
            }
        });

        // Check for required subforms
        $('.inline-form.add-row.required').each(function() {
            // Ensure these get validated whether or not they are changed
            inline_mark_changed(this);
            inline_catch_submit(this);
        });

        // Listen to Events
        inline_form_events();
        inline_button_events();
        inline_checkbox_events();
        inline_multiselect_events();
        inline_locationselector_events();
    });
});
