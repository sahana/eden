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
        if (msg) {
            S3.showAlert(msg, 'success')
            window.setTimeout('redirect_refresh()', 5000);
        }
    });
}
