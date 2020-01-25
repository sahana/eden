/**
 * Used in STL template, dvr/person controller, case activity tab
 */

(function($, undefined) {

    "use strict";

    var completed = '#dvr_case_activity_completed',
        endDate = '#dvr_case_activity_end_date',
        endDateRow = '#dvr_case_activity_end_date__row';

    var toggleEndDateRow = function() {

        var $endDate = $(endDate);

        if ($(completed).val() == 'False') {
            if ($endDate.calendarWidget('instance')) {
                $endDate.calendarWidget('clear');
            } else {
                $endDate.val('');
            }
            $(endDateRow).hide();
        } else {
            $(endDateRow).removeClass('hide').show();
        }
    };

    $(document).ready(function() {

        // Toggle end_date input dependent on completed-flag
        // (only if end_date is writable)
        if ($(completed).length && $(endDate).length) {
            $(completed).on('change', function() {
                toggleEndDateRow();
            });
            toggleEndDateRow();
        }
    });

})(jQuery);

// END ========================================================================
