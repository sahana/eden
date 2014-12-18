/**
 * Used by the Hrm Form (modules/s3db/hrm.py)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

// Module pattern to hide internal vars
(function () {

    var hrm_credential_start_date,
    hrm_credential_end_date,
    parts;
    var start_date_selector = "#hrm_credential_start_date";
    var end_date_selector = "#hrm_credential_end_date";

    var end_date_automate = function() {
        hrm_credential_start_date = $(start_date_selector).datepicker('getDate');

        // Add the days to the start_date and store in end_date.
        hrm_credential_start_date.setDate(hrm_credential_start_date.getDate()+hrm_end_date_days);
        hrm_credential_start_date = $.datepicker.formatDate(date_format, hrm_credential_start_date);
        $(end_date_selector).val(hrm_credential_start_date);
    };

    $(document).ready(function() {
        hrm_credential_end_date = $(end_date_selector).val();

        // Checks if Expiry Date is already Set or not. If it is, Then disables updation based on start date.
        if (hrm_credential_end_date == "") {
            end_date_automate();
            $(start_date_selector).change(end_date_automate);
        }
    });

}());
// END ========================================================================
