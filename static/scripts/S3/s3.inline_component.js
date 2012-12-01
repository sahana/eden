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
            field_id = '#sub_' +
                       formname + '_' + formname + '_i_' +
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
    };

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
    }

    // Enable the add-row
    function enable_inline_add(formname)
    {
        $('#add-row-'+formname +' > td > input').removeAttr('disabled');
        $('#add-row-'+formname +' > td > select').removeAttr('disabled');
        $('#add-row-'+formname +' > td > textarea').removeAttr('disabled');
        $('#add-row-'+formname +' > td > .inline-add').removeClass('hide');
    }

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
                      formname + '_' + formname + '_i_' +
                      fieldname + '_edit_' + rowindex;
            if ($(element).attr('type') == 'file') {
                // Store the upload at the end of the form
                form = $(element).closest('form');
                upload = $(element).clone();
                upload_id = 'upload_' + formname + '_' + fieldname + '_' + rowindex;
                $('#'+upload_id).remove();
                upload.attr('id', upload_id);
                upload.attr('name', upload_id);
                upload.css({display: 'none'});
                form.append(upload);
            }
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
    }

    // Validate a new/updated row
    function inline_validate(formname, rowindex, data, row) {

        // Construct the URL
        var c = data['controller'];
        var f = data['function'];
        var url = S3.Ap.concat('/' + c + '/' + f + '/validate.json');
        var resource = data['resource'];
        if (null !== resource && typeof resource != 'undefined') {
            url += '?resource='+resource;
            concat = '&';
        } else {
            concat = '?';
        }
        var component = data['component'];
        if (null !== component && typeof component != 'undefined') {
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

    }

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
            element = '#sub_' + formname + '_' + formname + '_i_' + fieldname + '_edit_0';
            // If the element is a select then we may need to add the option we're choosing
            var select = $('select'+element);
            if (select.length != 0) {
                var option = $('select' + element + ' option[value="' + value + '"]');
                if (option.length == 0) {
                    // This option does not exist in the select, so add it
                    // because otherwise val() won't work. Maybe the option
                    // gets added later by a script (e.g. FilterFieldChange)
                    select.append('<option value="' + value + '">-</option>');
                }
            }
            if ($(element).attr('type') != 'file') {
                $(element).val(value);
            } else {
                // Update the existing upload item, if there is one
                upload = $('#upload_' + formname + '_' + fieldname + '_' + rowindex);
                if (upload.length) {
                    var id = $(element).attr('id');
                    var name = $(element).attr('name');
                    $(element).replaceWith(upload);
                    upload.attr('id', id);
                    upload.attr('name', name);
                    upload.css({display: ''});
                }
            }
            // Populate text in autocompletes
            text =  row[fieldname]['text'];
            element = '#dummy_sub_' + formname + '_' + formname + '_i_' + fieldname + '_edit_0';
            $(element).val(text);
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

        // Reset catch-submit
        inline_catch_submit(false, 'none', 'none');
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

        var success = false;
        if (null !== new_row) {
            success = true;
            // Add a new row to the real_input JSON
            new_row['_changed'] = true; // mark as changed
            newindex = data['data'].push(new_row) - 1;
            new_row['_index'] = newindex;
            inline_serialize(formname, data);

            // Create a new read-row, clear add-row
            read_row = '<tr id="read-row-'+formname+'-'+newindex+'" class="read-row">';
            fields = data['fields'];
            for (i=0; i<fields.length; i++) {
                field = fields[i]['name'];
                // Update all uploads to the new index
                upload = $('#upload_' + formname + '_' + field + '_none');
                if (upload.length) {
                    upload_id = 'upload_' + formname + '_' + field + '_' + newindex;
                    $('#'+upload_id).remove();
                    upload.attr('id', upload_id);
                    upload.attr('name', upload_id);
                }
                read_row += '<td>' + new_row[field]['text'] + '</td>';
                // Reset add-field to default value
                var d = $('#sub_' + formname + '_' + formname + '_i_' + field + '_edit_default');
                var f = $('#sub_' + formname + '_' + formname + '_i_' + field + '_edit_none');
                if (f.attr('type') == 'file') {
                    var empty = d.clone();
                    empty.attr('id', f.attr('id'));
                    empty.attr('name', f.attr('name'));
                    f.replaceWith(empty);
                } else {
                    default_value = d.val();
                    f.val(default_value);
                }
                default_value = $('#dummy_sub_' + formname + '_' + formname + '_i_' + field + '_edit_default').val();
                $('#dummy_sub_' + formname + '_' + formname + '_i_' + field + '_edit_none').val(default_value);
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
            inline_button_events();
        }

        // Hide throbber, show add-button
        $('#throbber-' + formname + '-' + rowindex).addClass('hide');
        $('#add-' + formname + '-' + rowindex).removeClass('hide');
        return (success);
    };

    // Update row
    inline_update = function(formname, rowindex) {
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
        if (null != new_row) {
            success = true;

            // Update the row in the real_input JSON
            new_row['_id'] = data['data'][rowindex]['_id'];
            new_row['_changed'] = true; // mark as changed
            new_row['_index'] = rowindex;
            data['data'][rowindex] = new_row;
            inline_serialize(formname, data);

            // Update read-row in the table, clear edit-row
            read_row = '';
            fields = data['fields'];
            for (i=0; i<fields.length; i++) {
                field = fields[i]['name'];
                read_row += '<td>' + new_row[field]['text'] + '</td>';
                // Reset edit-field to default value
                var d = $('#sub_' + formname + '_' + formname + '_i_' + field + '_edit_default');
                var f = $('#sub_' + formname + '_' + formname + '_i_' + field + '_edit_0');
                if (f.attr('type') == 'file') {
                    var empty = d.clone();
                    empty.attr('id', f.attr('id'));
                    empty.attr('name', f.attr('name'));
                    f.replaceWith(empty);
                } else {
                    default_value = d.val();
                    f.val(default_value);
                }
                default_value = $('#dummy_sub_' + formname + '_' + formname + '_i_' + field + '_edit_default').val();
                $('#dummy_sub_' + formname + '_' + formname + '_i_' + field + '_edit_0').val(default_value);
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
        data = inline_deserialize(formname);
        data['data'][rowindex]['_delete'] = true;
        inline_serialize(formname, data);

        // Remove the read-row for this item
        $('#read-row-'+rowname).remove();

        // Remove all uploads for this item
        $('input[name^="' + 'upload_' + formname + '_"][name$="_' + rowindex + '"]').remove();

        return true;
    };

    // Event handlers ---------------------------------------------------------

    // Submit the inline form which has currently the focus
    inline_row_submit = function() {
        if ('none' != inline_current_formname) {
            var success = false;
            if ('none' == inline_current_rowindex) {
                success = inline_add(inline_current_formname);
            } else {
                success = inline_update(inline_current_formname, inline_current_rowindex);
            }
            if (success) {
                var subform_id = '#sub-' + inline_current_formname;
                inline_catch_submit(false, 'none', 'none');
                $(subform_id).closest('form').submit();
            }
        } else {
            return true;
        }
        return false;
    };

    // When an inline-form has focus, then pressing 'enter' should
    // submit this inline-form, and not the master form
    inline_catch_submit = function(toggle, formname, rowindex) {
        if (toggle) {
            inline_current_formname = formname;
            inline_current_rowindex = rowindex;
            $('form').unbind('submit', inline_row_submit);
            $('form').bind('submit', inline_row_submit);
        } else {
            inline_current_formname = 'none';
            inline_current_rowindex = 'none';
            $('form').unbind('submit', inline_row_submit);
        }
    };

    // Events -----------------------------------------------------------------

    inline_form_events = function(id) {

        // Enforce submission of the inline-row if changed
        var enforce_inline_submit = function(i, add) {
            var subform = $(i).parent().parent();
            var names = subform.attr('id').split('-');
            var rowindex = subform.data('rowindex');
            if (add) {
                rowindex = 'none';
            }
            inline_catch_submit(true, names.pop(), rowindex);
        };
        $('.edit-row input[type="text"], .edit-row textarea').bind('input', function() {
            enforce_inline_submit(this, false);
        });
        $('.edit-row input[type!="text"], .edit-row select').bind('focusin', function() {
            $('.edit-row input[type!="text"], .edit-row select').one('change', function() {
                enforce_inline_submit(this, false);
            });
        });
        $('.add-row input[type="text"], .add-row textarea').bind('input', function() {
            enforce_inline_submit(this, true);
        });
        $('.add-row input[type!="text"], .add-row select').bind('focusin', function() {
            $('.add-row input[type!="text"], .add-row select').one('change', function() {
                enforce_inline_submit(this, true);
            });
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

    inline_button_events = function() {

        $('.inline-add').unbind('click');
        $('.inline-add').click(function() {
            var names = $(this).attr('id').split('-');
            var rowindex = names.pop();
            var formname = names.pop();
            var success = inline_add(formname);
            if (success) {
                inline_catch_submit(false, 'none', 'none');
            }
            return false;
        });
        $('.inline-cnc').unbind('click');
        $('.inline-cnc').click(function() {
            var names = $(this).attr('id').split('-');
            var zero = names.pop();
            var formname = names.pop();
            var rowindex = $('#edit-row-'+formname).data('rowindex');
            inline_cancel(formname, rowindex);
            inline_catch_submit(false, 'none', 'none');
            return false;
        });
        $('.inline-rdy').unbind('click');
        $('.inline-rdy').click(function() {
            var names = $(this).attr('id').split('-');
            var zero = names.pop();
            var formname = names.pop();
            var rowindex = $('#edit-row-'+formname).data('rowindex');
            var success = inline_update(formname, rowindex);
            if (success) {
                inline_catch_submit(false, 'none', 'none');
            }
            return false;
        });
        $('.inline-edt').unbind('click');
        $('.inline-edt').click(function() {
            var names = $(this).attr('id').split('-');
            var rowindex = names.pop();
            var formname = names.pop();
            inline_edit(formname, rowindex);
            inline_catch_submit(false, 'none', 'none');
            return false;
        });
        $('.inline-rmv').unbind('click');
        $('.inline-rmv').click(function() {
            var names = $(this).attr('id').split('-');
            var rowindex = names.pop();
            var formname = names.pop();
            inline_remove(formname, rowindex);
            inline_catch_submit(false, 'none', 'none');
            return false;
        });
    };
    inline_button_events();
});
