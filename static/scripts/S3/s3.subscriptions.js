/**
 * Used by the 'Subscriptions' page (templates/SAMBRO/controllers.py)
 * This script is in Static to allow caching
 */

$(document).ready(function(){
    var notification_options = $('#notification-options');
    notification_options.click(function() {
        notification_options.siblings().toggle();
        notification_options.children().toggle();
    });
    notification_options.siblings().toggle();
    notification_options.children().toggle();
    $('#subscription-form').submit(function() {
        $('input[name="subscription-filters"]').val(JSON.stringify(S3.search.getCurrentFilters($(this))));
    });
});