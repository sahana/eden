function update_prepop_list() {
    data = {'template': $('#setup_deployment_template option:selected').text()};
    $.ajax({
        type: 'POST',
        url: S3.Ap.concat('/setup/prepop_setting'),
        data: data,
        dataType: 'json'
    })
    .done(function(prepop_options) {
        $('#sub_defaultinstance_defaultinstance_i_prepop_options_edit_none').html('');
        $.each(prepop_options, function(key, value) {
            $('#sub_defaultinstance_defaultinstance_i_prepop_options_edit_none')
                .append($('<option></option>')
                .attr('value', 'template:' + value)
                .text(value));
            });
    });
}

function redirect_refresh() {
    url = window.location.href
    id = url.match('deploy\/([0-9]+)\/')[1]
    window.location = S3.ap.concat('/setup/refresh/'+id)
}

function get_upgrade_status() {
    url = window.location.href
    id = url.match('deploy\/([0-9]+)\/')[1]

    $.ajax({
        type: 'POST',
        url: S3.Ap.concat('/setup/upgrade_status'),
        data: {'id': id},
        dataType: 'json',
    })
    .done(function(msg) {
        if(msg) {
            S3.showAlert(msg, 'success')
            window.setTimeout('redirect_refresh()', 5000);
        }
    });
}

$(document).ready(function() {
    if($('#setup_deployment_template').length) {
        update_prepop_list();
        $('#setup_deployment_template').change(update_prepop_list);
    }
});
