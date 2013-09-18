/**
 * Used by the pr/person 'Contacts' page (templates/DRMP/config.py)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

$(document).ready(function(){

    var more_button = $('.updates .dl-pagination');

    // If there are less than 4 Logs, hide the more button
    var items = $('.updates .dl-item').length;
    if (items < 4) {
        //more_button.hide();
    }

    // Make the 'more' button load a Modal
    var url = S3.Ap.concat('/default/audit/datalist');
    more_button.attr('href', url)
               .attr('title', 'Updates') // @ToDo: i18n if used outside of LA
               .addClass('s3_modal');
    S3.addModals();

});