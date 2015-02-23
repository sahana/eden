/* German initialisation for the timepicker plugin */
/* Written by Lowie Hulzinga. */
jQuery(function($){
    $.fgtimepicker.regional['de'] = {
                hourText: 'Stunde',
                minuteText: 'Minuten',
                amPmText: ['AM', 'PM'] ,
                closeButtonText: 'Beenden',
                nowButtonText: 'Aktuelle Zeit',
                deselectButtonText: 'Wischen' }
    $.fgtimepicker.setDefaults($.fgtimepicker.regional['de']);
});
