$(document).ready(function() {    
    $('.gis_print_map-btn').on('click', function() {
        if ($('#gis_print_help_popup').length) {
            $('#gis_print_help_popup').dialog('open');
        } else {
            $(this).append('<div id="gis_print_help_popup">' + i18n.gis_print_help + '</div>');
            $('#gis_print_help_popup').dialog({
                dialogClass: 'notitle',
                minHeight: 50
            });
        }
    })
});