(function() {

    /**
     * Function to make RDRT roster member status inline-editable
     *
     * @param {string} ajaxURL - the Ajax URL for the update request (POST)
     * @param {string} active - localized label for "active" option
     * @param {string} inactive - localized label for "inactive" option
     * @param {string} submit - localized label for submit button
     */
    $.rdrtStatus = function(ajaxURL, active, inactive, submit) {

        var options = {'0': inactive, '1': active};

        $('#rdrt-roster-status').editable(function(value) {

            var currentStatus = $(this).data('status'),
                active = false;
            if (value == 1) {
                active = true;
            }
            $.ajaxS3({
                type: 'POST',
                url: ajaxURL,
                data: JSON.stringify({'$_deploy_application': {'active': active}}),
                dataType: 'JSON',
                async: false,
                success: function(response) {
                    if (response.status == 'success') {
                        currentStatus = value;
                    }
                }
            });
            $(this).data('status', currentStatus);
            return options[currentStatus];

        }, {data: function() {
                return JSON.stringify($.extend({'selected': $(this).data('status')}, options));
            },
            type: 'select',
            style: 'display: inline',
            submit: submit
        });
    };
})(jQuery);
