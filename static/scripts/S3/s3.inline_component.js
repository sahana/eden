/**
 * Used by S3SQLInlineComponentField (modules/s3forms.py)
 */

$(function() {

    var inline_current_formname = 'none';
    var inline_current_rowindex = 'none';

    // Utilities --------------------------------------------------------------

    // Get the real input name
    inline_get_field = function(formname) {
        var selector = '#sub-' + formname;
        var field = $(selector).attr('field');
        return field;
    };

    // Read JSON from real_input, decode and store as data object
    inline_deserialize = function(formname) {
        var real_input = '#' + inline_get_field(formname);
        data_json = $(real_input).val();
        data = JSON.parse(data_json);
        $(real_input).data('data', data);
        return data;
    };

    // Serialize the data object as JSON and store into real_input
    inline_serialize = function(formname) {
        var real_input = '#' + inline_get_field(formname);
        data = $(real_input).data('data');
        data_json = JSON.stringify(data);
        $(real_input).val(data_json);
        return data_json;
    };

    // Append an error to a form field or row
    inline_append_error = function(formname, rowindex, fieldname, message) {
        if (null == fieldname) {
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
            field_id = '#sub_' +
                       formname + '_' + formname + '_' +
                       fieldname + '_edit_' + rowindex;
            msg = '<div class="' + formname + '_error error">' +
                    message +
                  '</div>';
        }
        $(field_id).after(msg);
        $('.'+formname+'_error').hide();
        $('.error').click(function() {
            $(this).fadeOut('slow');
            return false;
        });
    };

    // Display all errors
    inline_display_errors = function(formname) {
        $('.'+formname+'_error').slideDown();
    }

    // Remove all error messages from the form
    inline_remove_errors = function(formname) {
        $('.'+formname+'_error').remove();
    };

    // Disable the add-row
    function disable_inline_add(formname)
    {
        $('#add-row-'+formname +' > td > input').attr('disabled', true);
        $('#add-row-'+formname +' > td > select').attr('disabled', true);
        $('#add-row-'+formname +' > td > textarea').attr('disabled', true);
        $('#add-row-'+formname +' > td > .inline-add').addClass('hide');
    };

    // Enable the add-row
    function enable_inline_add(formname)
    {
        $('#add-row-'+formname +' > td > input').removeAttr('disabled');
        $('#add-row-'+formname +' > td > select').removeAttr('disabled');
        $('#add-row-'+formname +' > td > textarea').removeAttr('disabled');
        $('#add-row-'+formname +' > td > .inline-add').removeClass('hide');
    };

    // Collect the data from the form
    function inline_collect_data(formname, data, rowindex) {

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
        var value;
        for (var i=0; i<fields.length; i++) {
            fieldname = fields[i]['name'];
            element = '#sub_' +
                      formname + '_' + formname + '_' +
                      fieldname + '_edit_' + rowindex;
            value = $(element).val();
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
    function inline_validate(formname, rowindex, data, row) {

        // Construct the URL
        var c = data['controller'];
        var f = data['function'];
        var url = S3.Ap.concat('/' + c + '/' + f + '/validate.json');
        var resource = data['resource'];
        if (null != resource && typeof resource != 'undefined') {
            url += '?resource='+resource;
            concat = '&';
        } else {
            concat = '?';
        }
        var component = data['component'];
        if (null != component && typeof component != 'undefined') {
            url += concat+'component='+component;
        }

        // Request validation of the row
        var row_json = JSON.stringify(row);
        var response = null;
        $.ajaxS3({
            type: 'POST',
            url: url,
            data: row_json,
            dataType: 'json',
            success: function(data) {
                response = data;
            },
            async: false
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

        // Return the validated+represented row
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
    inline_edit = function(formname, rowindex) {
        var rowname = formname + '-' + rowindex;

        inline_remove_errors(formname);

        // Hide the current read row, show all other read rows
        $('.read-row').removeClass('hide');
        $('#read-row-'+rowname).addClass('hide');

        // Populate the edit row with the data for this rowindex
        data = inline_deserialize(formname);
        fields = data['fields'];
        row = data['data'][rowindex];
        for (i=0; i<fields.length; i++) {
            fieldname = fields[i]['name'];
            value = row[fieldname]['value'];
            element = '#sub_' + formname + '_' + formname + '_' + fieldname + '_edit_0';
            $(element).val(value);
            // Populate text in autocompletes
            text =  row[fieldname]['text']
            element = '#dummy_sub_' + formname + '_' + formname + '_' + fieldname + '_edit_0';
            $(element).val(text);
        }

        // Insert the edit row after this read row
        $('#edit-row-' + formname).insertAfter('#read-row-' + rowname);

        // Remember the current row index in the edit row
        $('#edit-row-' + formname).data('rowindex', rowindex);

        // Show the edit row
        $('#edit-row-' + formname).removeClass('hide');

        // Disable the add-row while editing
        disable_inline_add(formname);
    };

    // Cancel editing a row
    inline_cancel = function(formname, rowindex) {
        var rowname = formname + '-' + rowindex;

        inline_remove_errors(formname);

        // Hide the edit-row
        $('#edit-row-'+formname).addClass('hide');

        // Reset the row index
        $('#edit-row-'+formname).data('rowindex', null);

        // Show the read-row
        $('#read-row-'+rowname).removeClass('hide');

        // Enable the add-row
        enable_inline_add(formname);
    };

    // Add a new row
    inline_add = function(formname) {
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

        if (null != new_row) {
            // Add a new row to the real_input JSON
            new_row['_changed'] = true; // mark as changed
            newindex = data['data'].push(new_row) - 1;
            inline_serialize(formname, data);

            // Create a new read-row, clear add-row
            read_row = '<tr id="read-row-'+formname+'-'+newindex+'" class="read-row">';
            fields = data['fields'];
            for (i=0; i<fields.length; i++) {
                field = fields[i]['name'];
                read_row += '<td>' + new_row[field]['text'] + '</td>';
                // Reset add-field to default value
                default_value = $('#sub_' + formname + '_' + formname + '_' + field + '_edit_default').val();
                $('#sub_' + formname + '_' + formname + '_' + field + '_edit_none').val(default_value);
                default_value = $('#dummy_sub_' + formname + '_' + formname + '_' + field + '_edit_default').val();
                $('#dummy_sub_' + formname + '_' + formname + '_' + field + '_edit_none').val(default_value);
            }
            // Add edit-button
            edit = '#edt-' + formname + '-none';
            if ($(edit).length != 0) {
                read_row += '<td><a id="edt-' +
                            formname + '-' +
                            newindex + '" class="inline-edt" href="#">' +
                            $(edit).html() +
                            '</a></td>';
            } else {
                read_row += '<td></td>';
            }
            // Add remove-button
            remove = '#rmv-' + formname + '-none';
            if ($(remove).length != 0) {
                read_row += '<td><a id="rmv-' +
                            formname + '-' +
                            newindex + '" class="inline-rmv" href="#">' +
                            $(remove).html() +
                            '</a></td>';
            } else {
                read_row += '<td></td>';
            }
            read_row += '</tr>';
            // Append the new read-row to the table
            $('#sub-'+formname+' > table.embeddedComponent > tbody').append(read_row);
            inline_form_events();
        }

        // Hide throbber, show add-button
        $('#throbber-' + formname + '-' + rowindex).addClass('hide')
        $('#add-' + formname + '-' + rowindex).removeClass('hide')
    };

    // Update row
    inline_update = function(formname, rowindex) {
        var rowname = formname + '-' + rowindex;

        // Hide rdy, show throbber
        $('#rdy-' + formname + '-0').addClass('hide')
        $('#throbber-' + formname + '-0').removeClass('hide');

        // Remove any previous error messages
        inline_remove_errors(formname);

        // Collect the values from the edit-row
        var data = inline_deserialize(formname);
        var edit_row = inline_collect_data(formname, data, '0');

        // Validate the form data
        var new_row = inline_validate(formname, '0', data, edit_row);

        if (null != new_row) {
            // Update the row in the real_input JSON
            new_row['_id'] = data['data'][rowindex]['_id'];
            new_row['_changed'] = true; // mark as changed
            data['data'][rowindex] = new_row;
            inline_serialize(formname, data);

            // Update read-row in the table, clear edit-row
            read_row = '';
            fields = data['fields'];
            for (i=0; i<fields.length; i++) {
                field = fields[i]['name'];
                read_row += '<td>' + new_row[field]['text'] + '</td>';
                // Reset edit-field to default value
                default_value = $('#sub_' + formname + '_' + formname + '_' + field + '_edit_default').val();
                $('#sub_' + formname + '_' + formname + '_' + field + '_edit_0').val(default_value);
                default_value = $('#dummy_sub_' + formname + '_' + formname + '_' + field + '_edit_default').val();
                $('#dummy_sub_' + formname + '_' + formname + '_' + field + '_edit_0').val(default_value);
            }
            // Add edit-button
            edit = '#edt-' + formname + '-none';
            if ($(edit).length != 0) {
                read_row += '<td><a id="edt-' +
                            formname + '-' +
                            rowindex + '" class="inline-edt" href="#">' +
                            $(edit).html() +
                            '</a></td>';
            } else {
                read_row += '<td></td>';
            }
            // Add remove-button
            remove = '#rmv-' + formname + '-none';
            if ($(remove).length != 0) {
                read_row += '<td><a id="rmv-' +
                            formname + '-' +
                            rowindex + '" class="inline-rmv" href="#">' +
                            $(remove).html() +
                            '</a></td>';
            } else {
                read_row += '<td></td>';
            }

            $('#read-row-' + formname + '-' + rowindex + ' > td').remove();
            $('#read-row-' + formname + '-' + rowindex).html(read_row);
            inline_form_events();

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
    }

    // Remove a row
    inline_remove = function(formname, rowindex) {
        var rowname = formname + '-' + rowindex;

        // Confirmation dialog
        if (!confirm(S3.i18n.delete_confirmation)) {
            return false;
        }

        // Update the real_input JSON with deletion of this row
        data = inline_deserialize(formname);
        data['data'][rowindex]['_delete'] = true;
        inline_serialize(formname, data);

        // Remove the read-row for this item
        $('#read-row-'+rowname).remove();
    };

    // Event handlers ---------------------------------------------------------

    // Submit the inline form which has currently the focus
    inline_row_submit = function() {
        if ('none' != inline_current_formname) {
            if ('none' == inline_current_rowindex) {
                inline_add(inline_current_formname);
            } else {
                inline_update(inline_current_formname, inline_current_rowindex);
            }
        } else {
            return true;
        }
        return false;
    };

    // When an inline-form has focus, then pressing 'enter' should
    // submit this inline-form, and not the master form
    inline_catch_submit = function(toggle) {
        if (toggle) {
            $('form').unbind('submit', inline_row_submit);
            $('form').bind('submit', inline_row_submit);
        } else {
            $('form').unbind('submit', inline_row_submit);
        }
    };

    // Events -----------------------------------------------------------------

    inline_form_events = function() {
        $('.edit-row').unbind('focusin');
        $('.edit-row').focusin(function() {
            names = $(this).attr('id').split('-');
            inline_current_formname = names.pop();
            inline_current_rowindex = $(this).data('rowindex');
            inline_catch_submit(true);
        });
        $('.edit-row').unbind('focusout');
        $('.edit-row').focusout(function() {
            inline_current_formname = 'none';
            inline_current_rowindex = 'none';
            inline_catch_submit(false);
        });
        $('.add-row').unbind('focusin');
        $('.add-row').focusin(function() {
            names = $(this).attr('id').split('-');
            inline_current_formname = names.pop();
            inline_current_rowindex = 'none';
            inline_catch_submit(true);
        });
        $('.add-row').unbind('focusout');
        $('.add-row').focusout(function() {
            inline_current_formname = 'none';
            inline_current_rowindex = 'none';
            inline_catch_submit(false);
        });
        $('.inline-add').unbind('click');
        $('.inline-add').click(function() {
            names = $(this).attr('id').split('-');
            rowindex = names.pop();
            formname = names.pop();
            inline_add(formname);
            return false;
        });
        $('.inline-cnc').unbind('click');
        $('.inline-cnc').click(function() {
            names = $(this).attr('id').split('-');
            zero = names.pop();
            formname = names.pop();
            rowindex = $('#edit-row-'+formname).data('rowindex');
            inline_cancel(formname, rowindex);
            return false;
        });
        $('.inline-rdy').unbind('click');
        $('.inline-rdy').click(function() {
            names = $(this).attr('id').split('-');
            zero = names.pop();
            formname = names.pop();
            rowindex = $('#edit-row-'+formname).data('rowindex');
            inline_update(formname, rowindex);
            return false;
        });
        $('.inline-edt').unbind('click');
        $('.inline-edt').click(function() {
            names = $(this).attr('id').split('-');
            rowindex = names.pop();
            formname = names.pop();
            inline_edit(formname, rowindex);
            return false;
        });
        $('.inline-rmv').unbind('click');
        $('.inline-rmv').click(function() {
            names = $(this).attr('id').split('-');
            rowindex = names.pop();
            formname = names.pop();
            inline_remove(formname, rowindex);
            return false;
        });
    };
    inline_form_events();
});
