/* Swedish initialisation for the timepicker plugin */
/* Written by Björn Westlin (bjorn.westlin@su.se). */
jQuery(function($){
    $.fgtimepicker.regional['sv'] = {
                hourText: 'Timme',
                minuteText: 'Minut',
                amPmText: ['AM', 'PM'] ,
                closeButtonText: 'Stäng',
                nowButtonText: 'Nu',
                deselectButtonText: 'Rensa' }
    $.fgtimepicker.setDefaults($.fgtimepicker.regional['sv']);
});
