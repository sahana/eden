(function() {

    /**
     * Function to make RDRT roster member organisation inline-editable
     * using jquery.jeditable.js
     *
     * @param {string} ajaxURL - the Ajax URL for the update request (POST)
     * @param {string} submit - localized label for submit button
     */
    $.rdrtOrg = function(ajaxURL, submit) {

        var options = {};

        $('#rdrt-organisation').editable(function(value) {

            var currentOrg = $(this).data('organisation_id');

            $.ajaxS3({
                type: 'POST',
                url: ajaxURL.concat('?organisation_id=', value),
                async: false,
                success: function(response) {
                    if (response.status == 'success') {
                        currentOrg = value;
                    }
                }
            });

            $(this).data('organisation_id', currentOrg);
            return options[currentOrg]['name'];

        }, {
            data: function() {
                $.ajaxS3({
                    type: 'GET',
                    url: S3.Ap.concat('/deploy/human_resource/options.json?field=organisation_id'),
                    dataType: 'JSON',
                    async: false,
                    success: function(response) {
                        options = response;
                    }
                });
                return JSON.stringify($.extend({'selected': $(this).data('organisation_id')}, options));
            },
            type: 'select',
            style: 'display: inline',
            submit: submit
        });
    };

    /**
     * Function to make RDRT roster member status inline-editable
     * using jquery.jeditable.js
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

        }, {
            data: function() {
                return JSON.stringify($.extend({'selected': $(this).data('status')}, options));
            },
            type: 'select',
            style: 'display: inline',
            submit: submit
        });
    };

    /**
     * Function to make RDRT member human_resource.type inline-editable
     * using jquery.jeditable.js
     *
     * @param {string} ajaxURL - the Ajax URL for the update request (POST)
     * @param {string} staff - localized label for "staff" option
     * @param {string} volunteer - localized label for "volunteer" option
     * @param {string} submit - localized label for submit button
     */
    $.rdrtType = function(ajaxURL, staff, volunteer, submit) {

        var options = {'1': staff, '2': volunteer};

        $('#rdrt-resource-type').editable(function(value) {

            var currentType = $(this).data('type'),
                type = 1;
            if (value == 2) {
                type = 2;
            }

            $.ajaxS3({
                type: 'POST',
                url: ajaxURL,
                data: JSON.stringify({'$_hrm_human_resource': {'type': type}}),
                dataType: 'JSON',
                async: false,
                success: function(response) {
                    if (response.status == 'success') {
                        currentType = value;
                    }
                }
            });

            $(this).data('type', currentType);
            return options[currentType];

        }, {
            data: function() {
                return JSON.stringify($.extend({'selected': $(this).data('type')}, options));
            },
            type: 'select',
            style: 'display: inline',
            submit: submit
        });
    };

})(jQuery);
