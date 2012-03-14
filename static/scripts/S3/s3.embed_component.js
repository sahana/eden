/**
 * Used by S3EmbedComponentWidget (modules/s3widgets.py)
 */

$(function() {

    var controller = $('#select_from_registry_row').attr('controller');
    var component = $('#select_from_registry_row').attr('component');
    var url = $('#select_from_registry_row').attr('url');
    var value = $('#select_from_registry_row').attr('value');
    var fieldname = $('#select_from_registry_row').attr('field');
    var real_input = '#' + fieldname;
    var dummyname = 'dummy_' + fieldname;
    var dummy_input = '#' + dummyname;
    var component_id = $(real_input).val();

    $(dummy_input).addClass('hide');

    if (component_id > 0) {
        // If an ID present then disable input fields
        $('#clear_form_link').removeClass('hide');
        $('#edit_selected_link').removeClass('hide');
        disable_embedded();
    }
    // Set up Listeners
    $('#select_from_registry').click(function() {
        $('#select_from_registry_row').addClass('hide');
        $('#component_autocomplete_row').removeClass('hide');
        $(dummy_input).removeClass('hide');
        $('#component_autocomplete_label').removeClass('hide');
        $(dummy_input).focus();
    });
    $(dummy_input).focusout(function() {
        component_id = $(real_input).val()
        $(dummy_input).addClass('hide');
        $('#component_autocomplete_label').addClass('hide');
        $('#select_from_registry_row').removeClass('hide');
        if (component_id > 0) {
             $('#clear_form_link').removeClass('hide');
        }
    });
    clear_component_form = function() {
        enable_embedded();
        $(real_input).val('');
        $('.embedded > td > input').val('');
        $('.embedded > td > select').val('');
        $('.embedded > td > textarea').val('');
        $('#clear_form_link').addClass('hide');
        $('#edit_selected_link').addClass('hide');
    }
    edit_selected_form = function() {
        enable_embedded();
        $('#edit_selected_link').addClass('hide');
    }
    // Called on post-process by the Autocomplete Widget
    select_component = function(component_id) {
        $('#select_from_registry').addClass('hide');
        $('#clear_form_link').addClass('hide');
        $('#load_throbber').removeClass('hide');
        clear_component_form()
        var json_url = url + component_id + '.s3json?show_ids=true';
        $.getJSONS3(json_url, function (data) {
            try {
                var record = data['$_'+component][0]
                disable_embedded();
                $(real_input).val(record['@id']);
                var re = new RegExp("^[\$|\@].*");
                var fk = new RegExp("^[\$]k_.*");
                for (j in record) {
                    if (j.match(re)) {
                        if (j.match(fk)) {
                            var field_id = '#' + component + "_" + j.slice(3);
                        } else {
                            continue;
                        }
                    } else {
                        var field_id = '#' + component + "_" + j;
                    }
                    try {
                        data = record[j]
                        if (data.hasOwnProperty('@id')) {
                            var id = eval(data['@id']);
                            $(field_id).val(id);
                        } else
                        if (data.hasOwnProperty('@value')) {
                            try {
                                val = JSON.parse(data['@value']);
                            }
                            catch(e) {
                                val = data['@value'];
                            }
                            $(field_id).val(val);
                        }
                        else {
                            $(field_id).val(data);
                        }
                    }
                    catch(e) {
                        // continue
                    }
                };
            }
            catch(e) {
                $(real_input).val('');
            }
            $('#load_throbber').addClass('hide');
            $('#select_from_registry').removeClass('hide');
            $('#clear_form_link').removeClass('hide');
            $('#edit_selected_link').removeClass('hide');
        });
        $('#component_autocomplete_row').addClass('hide');
        $('#select_from_registry_row').removeClass('hide');
    };
    if (value != 'None') {
        $(real_input).val(value);
        select_component(value);
    }
    $('form').submit( function() {
        // The form is being submitted

        // Do the normal form-submission tasks
        // @ToDo: Look to have this happen automatically
        // http://forum.jquery.com/topic/multiple-event-handlers-on-form-submit
        // http://api.jquery.com/bind/
        S3ClearNavigateAwayConfirm();

        // Ensure that all fields aren't disabled (to avoid wiping their contents)
        enable_embedded();

        // Allow the Form's Save to continue
        return true;
    });
    function hide_embedded()
    {
        $('.embedded').addClass('hide');
    };
    function show_embedded()
    {
        $('.embedded').removeClass('hide');
    };
    function enable_embedded()
    {
        $('.embedded > td > input').removeAttr('disabled');
        $('.embedded > td > select').removeAttr('disabled');
        $('.embedded > td > textarea').removeAttr('disabled');
    };
    function disable_embedded()
    {
        $('.embedded > td > input').attr('disabled', true);
        $('.embedded > td > select').attr('disabled', true);
        $('.embedded > td > textarea').attr('disabled', true);
    };
});
