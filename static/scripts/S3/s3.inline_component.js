/**
 * Used by S3SQLInlineComponent (modules/s3forms.py)
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
        var real_input = '#' + inline_get_field(formname);
        var data_json = $(real_input).val();
        var data = JSON.parse(data_json);
        $(real_input).data('data', data);
        return data;
    };

    // Serialize the data object as JSON and store into real_input
    var inline_serialize = function(formname) {
        var real_input = '#' + inline_get_field(formname);
        var data = $(real_input).data('data');
        var data_json = JSON.stringify(data);
        $(real_input).val(data_json);
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
            l = $(field_id + '> td').length;
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
        $('.' + formname + '_error').slideDown();
    };

    // Remove all error messages from the form
    var inline_remove_errors = function(formname) {
        $('.' + formname + '_error').remove();
    };

    // Disable the add-row
    var disable_inline_add = function(formname) {
        $('#add-row-' + formname + ' > td input').prop('disabled', true);
        $('#add-row-' + formname + ' > td select').prop('disabled', true);
        $('#add-row-' + formname + ' > td textarea').prop('disabled', true);
        $('#add-row-' + formname + ' > td .inline-add').addClass('hide');
        $('#add-row-' + formname + ' > td .action-lnk').addClass('hide');
    };

    // Enable the add-row
    var enable_inline_add = function(formname) {
        $('#add-row-' + formname + ' > td input').prop('disabled', false);
        $('#add-row-' + formname + ' > td select').prop('disabled', false);
        $('#add-row-' + formname + ' > td textarea').prop('disabled', false);
        $('#add-row-' + formname + ' > td .inline-add').removeClass('hide');
        $('#add-row-' + formname + ' > td .action-lnk').removeClass('hide');
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
        var fields = data['fields'];
        var fieldname;
        var element;
        var input;
        var value;
        var cssclass;
        var intvalue;
        for (var i=0; i < fields.length; i++) {
            fieldname = fields[i]['name'];
            element = '#sub_' +
                      formname + '_' + formname + '_i_' +
                      fieldname + '_edit_' + rowindex;
            input = $(element);
            value = input.val();
            if (input.attr('type') == 'file') {
                // Store the upload at the end of the form
                var form = input.closest('form');
                var cloned = input.clone();
                var upload_id = 'upload_' + formname + '_' + fieldname + '_' + rowindex;
                $('#' + upload_id).remove();
                if (value.match(/fakepath/)) {
                    // IE, etc: Remove 'fakepath' from filename
                    value = value.replace(/(c:\\)*fakepath\\/i, '');
                }
                // Clone the Input ready for any additional files
                cloned.insertAfter(input);
                // We move the original input as it doesn't contain the file otherwise on IE, etc
                // http://stackoverflow.com/questions/415483/clone-a-file-input-element-in-javascript
                input.css({display: 'none'})
                     .attr('id', upload_id)
                     .attr('name', upload_id)
                     .appendTo(form);
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
            row[fieldname] = value;
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
        var row_json = JSON.stringify(row);
        var response = null;
        $.ajaxS3({
            async: false,
            type: 'POST',
            url: url,
            data: row_json,
            dataType: 'json',
            // gets moved to .done() inside .ajaxS3
            success: function(data) {
                response = data;
            }
        });

        // Check and report errors
        var has_errors = false;
        if (response.hasOwnProperty('_error')) {
            has_errors = true;
            inline_append_error(formname, rowindex, null, response['_error']);
        }
        for (field in response) {
            var item = response[field];
            if (item.hasOwnProperty('_error')) {
                inline_append_error(formname, rowindex, field, item['_error']);
                has_errors = true;
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

        // Hide the current read row, show all other read rows
        $('.read-row').removeClass('hide');
        $('#read-row-' + rowname).addClass('hide');

        // Populate the edit row with the data for this rowindex
        var data = inline_deserialize(formname);
        var fields = data['fields'];
        var row = data['data'][rowindex];
        var fieldname;
        var value;
        var element;
        var input;
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
            if (input.attr('type') != 'file') {
                input.val(value);
                // Populate text in autocompletes
                element = '#dummy_sub_' + formname + '_' + formname + '_i_' + fieldname + '_edit_0';
                var text = row[fieldname]['text'];
                $(element).val(text);
            } else {
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
            }
        }

        // Insert the edit row after this read row
        $('#edit-row-' + formname).insertAfter('#read-row-' + rowname);

        // Remember the current row index in the edit row
        $('#edit-row-' + formname).data('rowindex', rowindex);

        // Show the edit row
        $('#edit-row-' + formname).removeClass('hide');
        $('#edit-row-' + formname + ' select').change();

        // Disable the add-row while editing
        disable_inline_add(formname);
    };

    // Cancel editing a row
    var inline_cancel = function(formname, rowindex) {
        var rowname = formname + '-' + rowindex;

        inline_remove_errors(formname);

        var $edit = $('#edit-row-' + formname);
        
        // Hide and reset the edit-row
        $edit.addClass('hide')
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

        // Hide add-button, show throbber
        $('#add-' + formname + '-' + rowindex).addClass('hide');
        $('#throbber-' + formname + '-' + rowindex).removeClass('hide');

        // Remove any previous error messages
        inline_remove_errors(formname);

        // Collect the values from the add-row
        var data = inline_deserialize(formname);
        var add_row = inline_collect_data(formname, data, 'none');

        // Validate the data
        var new_row = inline_validate(formname, rowindex, data, add_row);

        var success = false;
        if (null !== new_row) {
            success = true;
            // Add a new row to the real_input JSON
            new_row['_changed'] = true; // mark as changed
            var newindex = data['data'].push(new_row) - 1;
            new_row['_index'] = newindex;
            inline_serialize(formname, data);

            // Create a new read-row, clear add-row
            var read_row = '<tr id="read-row-' + formname + '-' + newindex + '" class="read-row">';
            var fields = data['fields'];
            var default_value;
            for (i=0; i < fields.length; i++) {
                var field = fields[i]['name'];
                // Update all uploads to the new index
                var upload = $('#upload_' + formname + '_' + field + '_none');
                if (upload.length) {
                    var upload_id = 'upload_' + formname + '_' + field + '_' + newindex;
                    $('#' + upload_id).remove();
                    upload.attr('id', upload_id)
                          .attr('name', upload_id);
                }
                read_row += '<td>' + new_row[field]['text'] + '</td>';
                // Reset add-field to default value
                var d = $('#sub_' + formname + '_' + formname + '_i_' + field + '_edit_default');
                var f = $('#sub_' + formname + '_' + formname + '_i_' + field + '_edit_none');
                if (f.attr('type') == 'file') {
                    var empty = d.clone();
                    empty.attr('id', f.attr('id'))
                         .attr('name', f.attr('name'));
                    f.replaceWith(empty);
                } else {
                    default_value = d.val();
                    f.val(default_value);
                }
                default_value = $('#dummy_sub_' + formname + '_' + formname + '_i_' + field + '_edit_default').val();
                $('#dummy_sub_' + formname + '_' + formname + '_i_' + field + '_edit_none').val(default_value);
            }
            // Unmark changed
            $('#add-row-' + formname).removeClass('changed');
            
            // Add edit-button
            var edit = '#edt-' + formname + '-none';
            if ($(edit).length !== 0) {
                read_row += '<td><div><div id="edt-' + formname + '-' + newindex + '" class="inline-edt"></div></div></td>';
            } else {
                read_row += '<td></td>';
            }
            // Add remove-button
            var remove = '#rmv-' + formname + '-none';
            if ($(remove).length !== 0) {
                read_row += '<td><div><div id="rmv-' + formname + '-' + newindex + '" class="inline-rmv"></div></div></td>';
            } else {
                read_row += '<td></td>';
            }
            read_row += '</tr>';
            // Append the new read-row to the table
            $('#sub-' + formname + ' > table.embeddedComponent > tbody').append(read_row);
            inline_button_events();
        }

        // Hide throbber, show add-button
        $('#throbber-' + formname + '-' + rowindex).addClass('hide');
        $('#add-' + formname + '-' + rowindex).removeClass('hide');
        return (success);
    };

    // Update row
    var inline_update = function(formname, rowindex) {
        var rowname = formname + '-' + rowindex;

        // Hide rdy, show throbber
        $('#rdy-' + formname + '-0').addClass('hide');
        $('#throbber-' + formname + '-0').removeClass('hide');

        // Remove any previous error messages
        inline_remove_errors(formname);

        // Collect the values from the edit-row
        var data = inline_deserialize(formname);
        var edit_row = inline_collect_data(formname, data, '0');

        // Validate the form data
        var new_row = inline_validate(formname, '0', data, edit_row);

        var success = false;
        if (null !== new_row) {
            success = true;

            // Update the row in the real_input JSON
            new_row['_id'] = data['data'][rowindex]['_id'];
            new_row['_changed'] = true; // mark as changed
            new_row['_index'] = rowindex;
            data['data'][rowindex] = new_row;
            inline_serialize(formname, data);

            // Update read-row in the table, clear edit-row
            var read_row = '';
            var fields = data['fields'];
            var default_value;
            for (i=0; i < fields.length; i++) {
                var field = fields[i]['name'];
                read_row += '<td>' + new_row[field]['text'] + '</td>';
                // Reset edit-field to default value
                var d = $('#sub_' + formname + '_' + formname + '_i_' + field + '_edit_default');
                var f = $('#sub_' + formname + '_' + formname + '_i_' + field + '_edit_0');
                if (f.attr('type') == 'file') {
                    var empty = d.clone();
                    empty.attr('id', f.attr('id'))
                         .attr('name', f.attr('name'));
                    f.replaceWith(empty);
                } else {
                    default_value = d.val();
                    f.val(default_value);
                }
                default_value = $('#dummy_sub_' + formname + '_' + formname + '_i_' + field + '_edit_default').val();
                $('#dummy_sub_' + formname + '_' + formname + '_i_' + field + '_edit_0').val(default_value);
            }
            // Unmark changed
            $('#edit-row-' + formname).removeClass('changed');
            
            // Add edit-button
            var edit = '#edt-' + formname + '-none';
            if ($(edit).length !== 0) {
                read_row += '<td><div><div id="edt-' + formname + '-' + rowindex + '" class="inline-edt"></div></div></td>';
            } else {
                read_row += '<td></td>';
            }
            // Add remove-button
            var remove = '#rmv-' + formname + '-none';
            if ($(remove).length !== 0) {
                read_row += '<td><div><div id="rmv-' + formname + '-' + rowindex + '" class="inline-rmv"></div></div></td>';
            } else {
                read_row += '<td></td>';
            }

            $('#read-row-' + formname + '-' + rowindex + ' > td').remove();
            $('#read-row-' + formname + '-' + rowindex).html(read_row);
            inline_button_events();

            // Hide and reset the edit row
            $('#edit-row-' + formname).addClass('hide');

            // Reset rowindex
            $('#edit-row-' + formname).data('rowindex', null);

            // Show the read row
            $('#read-row-' + rowname).removeClass('hide');

            // Re-enable add-row
            enable_inline_add(formname);

        }
        // Hide throbber, enable rdy
        $('#rdy-' + formname + '-0').removeClass('hide');
        $('#throbber-' + formname + '-0').addClass('hide');
        return (success);
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

        // Display the add-row (in case hidden because we're multiple=False)
        $('#add-row-' + formname).show();

        return true;
    };

    // Event handlers ---------------------------------------------------------

    // Submit all changed inline-rows, and then the main form
    var inline_submit_all = function() {
        var $form = $(this);
        var success = false;
        $form.find('tr.inline-form.changed').each(function() {
            var formname = $(this).attr('id').split('-').pop();
            if ($(this).hasClass('add-row')) {
                success = inline_add(formname);
            } else {
                var rowindex = $(this).data('rowindex');
                success = inline_update(formname, rowindex);
            }
        });
        if (success) {
            $('form').unbind('submit', inline_submit_all);
            $form.submit();
        }
    }
    
    // Catch form-submit if any inline-row has been changed
    var inline_catch_submit = function(toggle, element) {
        var form = $(element).closest('form');
        if (toggle) {
            $('form').unbind('submit', inline_submit_all)
                     .bind('submit', inline_submit_all);
        } else {
            $('form').unbind('submit', inline_submit_all);
        }
    }

    // Events -----------------------------------------------------------------

    var inline_form_events = function() {

        // Change-events
        $('.edit-row input[type="text"], .edit-row textarea').bind('input', function() {
            inline_mark_changed(this);
            inline_catch_submit(true, this);
        });
        $('.edit-row input[type!="text"], .edit-row select').bind('focusin', function() {
            $('.edit-row input[type!="text"], .edit-row select').one('change', function() {
                inline_mark_changed(this);
                inline_catch_submit(true, this);
            });
        });
        $('.add-row input[type="text"], .add-row textarea').bind('input', function() {
            inline_mark_changed(this);
            inline_catch_submit(true, this);
        });
        $('.add-row input[type!="text"], .add-row select').bind('focusin', function() {
            $('.add-row input[type!="text"], .add-row select').one('change', function() {
                inline_mark_changed(this);
                inline_catch_submit(true, this);
            });
        });
        // Chrome doesn't mark row as changed when just file input added
        $('.add-row input[type="file"]').change(function() {
            inline_mark_changed(this);
            inline_catch_submit(true, this);
        });

        // Submit the inline-row instead of the main form if pressing Enter
        $('.edit-row input').keypress(function(e) {
            if (e.which == 13) {
                e.preventDefault();
                return false;
            }
            return true;
        });
        $('.edit-row input').keyup(function(e) {
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
        });
        $('.add-row input').keyup(function(e) {
            if (e.which == 13) {
                var subform = $(this).parent().parent();
                var names = subform.attr('id').split('-');
                inline_add(names.pop());
            }
        });
    };
    inline_form_events();

    var inline_button_events = function() {

        $('.inline-add').unbind('click');
        $('.inline-add').click(function() {
            var names = $(this).attr('id').split('-');
            var rowindex = names.pop();
            var formname = names.pop();
            inline_add(formname);
            return false;
        });
        $('.inline-cnc').unbind('click');
        $('.inline-cnc').click(function() {
            var names = $(this).attr('id').split('-');
            var zero = names.pop();
            var formname = names.pop();
            var rowindex = $('#edit-row-' + formname).data('rowindex');
            inline_cancel(formname, rowindex);
            return false;
        });
        $('.inline-rdy').unbind('click');
        $('.inline-rdy').click(function() {
            var names = $(this).attr('id').split('-');
            var zero = names.pop();
            var formname = names.pop();
            var rowindex = $('#edit-row-' + formname).data('rowindex');
            inline_update(formname, rowindex);
            return false;
        });
        $('.inline-edt').unbind('click');
        $('.inline-edt').click(function() {
            var names = $(this).attr('id').split('-');
            var rowindex = names.pop();
            var formname = names.pop();
            inline_edit(formname, rowindex);
            return false;
        });
        $('.inline-rmv').unbind('click');
        $('.inline-rmv').click(function() {
            var names = $(this).attr('id').split('-');
            var rowindex = names.pop();
            var formname = names.pop();
            inline_remove(formname, rowindex);
            return false;
        });
    };
    inline_button_events();

    // Used by S3SQLInlineComponentCheckbox
    if ($('.error_wrapper').length) {
        // Errors in form, so ensure we show correct checkbox status
        var checkboxes = $('.inline-checkbox :checkbox');
        var that, value, names, formname, fieldname, data, _data, item, i;
        for (var c = 0; c < checkboxes.length; c++) {
            that = $(checkboxes[c]);
            value = that.val();
            names = that.attr('id').split('-');
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
                    that.prop('checked', true);
                } else if (item['_delete']) {
                    that.prop('checked', false);
                }
            }
        }
    }
    var inline_checkbox_events = function() {
        // Listen for changes on all Inline Checkboxes
        $('.inline-checkbox :checkbox').click(function() {
            var that = $(this);
            var value = that.val();
            var names = that.attr('id').split('-');
            var formname = names[1];
            var fieldname = names[2];
            // Read current data from real input
            var data = inline_deserialize(formname);
            var _data = data['data'];
            var item;
            for (var prop in _data) {
                var i = _data[prop];
                if (i.hasOwnProperty(fieldname) && i[fieldname]['value'] == value) {
                    item = i;
                    break;
                }
            }
            // Modify data
            if (that.prop('checked')) {
                if (!item) {
                    // Not yet found, so initialise
                    var label = that.next().html(); // May be fragile to different formstyles :/
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
    inline_checkbox_events();
});
