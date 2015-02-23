/* Nederlands initialisation for the timepicker plugin */
/* Written by Lowie Hulzinga. */
jQuery(function($){
    $.fgtimepicker.regional['nl'] = {
                hourText: 'Uren',
                minuteText: 'Minuten',
                amPmText: ['AM', 'PM'],
				closeButtonText: 'Sluiten',
				nowButtonText: 'Actuele tijd',
				deselectButtonText: 'Wissen' }
    $.fgtimepicker.setDefaults($.fgtimepicker.regional['nl']);
});