/**
 * Used in STL template, dvr/person controller
 */

(function($, undefined) {

    "use strict";

    var hohCheckbox = '#pr_person_sub_dvr_case_head_of_household'

    var toggleHoHFields = function() {

        var formFields = [
            'pr_person_sub_dvr_case_hoh_name',
            'pr_person_sub_dvr_case_hoh_gender',
            'pr_person_sub_dvr_case_hoh_relationship'
        ];

        var checkbox = $(hohCheckbox);
        if (checkbox.length && checkbox.is(':checked')) {
            for (var i=0, len=formFields.length; i<len; i++) {
                var formField = formFields[i];
                $('#' + formField + '__row').hide();
            }
        } else {
            for (var i=0, len=formFields.length; i<len; i++) {
                var formField = formFields[i];
                $('#' + formField + '__row').show();
            }
        }
    };

    /**
     * Document-ready functions for work/job datalist
     */
    $(document).ready(function() {

        $(hohCheckbox).unbind('.dvr').bind('click.dvr', function() {
            toggleHoHFields();
        });
        toggleHoHFields();

    });

})(jQuery);

// END ========================================================================
