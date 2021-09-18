/**
 * Register-shipment action for requests
 *
 * @copyright 2021 (c) Sahana Software Foundation
 * @license MIT
 */
(function($, undefined) {

    "use strict";

    $(document).ready(function() {

        var path = window.location.pathname.split('/'),
            confirmation = i18n.req_register_shipment;
        var handler = function() {
            if (!confirm || confirm(confirmation)) {
                var recordID = $(this).attr('db_id');
                if (recordID) {
                    var action = path.slice(0, 2).concat(['req', 'req', recordID, 'ship']).join('/'),
                        form = document.createElement('form');
                    // TODO include formkey in post-data
                    form.action = action;
                    form.method = 'POST';
                    form.target = '_self';
                    form.enctype = 'multipart/form-data';
                    form.style.display = 'none';
                    document.body.appendChild(form);
                    form.submit();
                }
            }
        };
        var dt = $('#datatable');
        if (dt.length) {
            // Datatable action-button
            dt.on('click', '.ship-btn', handler);
        } else {
            // Standalone action-button
            $('.ship-btn').on('click', handler);
        }
    });
})(jQuery);
