/**
 * Used by the 'News Feed' page (templates/DRMP/controllers.py)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

$(document).ready(function(){

    // Style the Search TextFilter widget
    $('#post-cms_post_body-text-filter__row').addClass('input-append')
                                             .append('<span class="add-on"><i class="icon-search"></i></span>');

    // Button to toggle Advanced Form
    $('#list-filter').append('<a class="accordion-toggle"><i class="icon-reorder"></i> ' + i18n.adv_search + '</a>');
    $('.accordion-toggle').click(function() {
        var advanced = $('.advanced');
        if (advanced.hasClass('hide')) {
            // Toggle doesn't work directly & requires a 2nd click to open
            advanced.removeClass('hide').show();
        } else {
            advanced.toggle();
        }
    })
});