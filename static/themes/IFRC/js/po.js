/**
 * Outreach module:
 * Progressive revelation of embedded components in household form
 */

(function() {

    /**
     * Function to display/hide embedded household components
     *
     * @param status: whether to show (true) or hide (false) the components
     */
    $.showHouseholdComponents = function(status) {

        var toggle_rows = ['#po_household_sub_defaultcontact__row',
                           '#po_household_sub_defaultcontact__row1',
                           '#po_household_sub_household_social_language__row',
                           '#po_household_sub_household_social_language__row1',
                           '#po_household_sub_household_social_community__row',
                           '#po_household_sub_household_social_community__row1'
                           ];
        if (status) {
            $(toggle_rows.join(',')).removeClass('hide').show();
        } else {
            $(toggle_rows.join(',')).hide();
        }
    };
})(jQuery);

$(document).ready(function() {

    $('#po_household_followup').off('.po')
                               .on('click.po', function() {
        $.showHouseholdComponents($(this).prop('checked'));
    });
    // Check initial state
    $.showHouseholdComponents($('#po_household_followup').prop('checked'));
});
