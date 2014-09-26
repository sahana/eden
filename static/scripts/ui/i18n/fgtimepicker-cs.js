/* Czech initialisation for the timepicker plugin */
/* Written by David Spohr (spohr.david at gmail). */
jQuery(function($){
    $.fgtimepicker.regional['cs'] = {
                hourText: 'Hodiny',
                minuteText: 'Minuty',
                amPmText: ['AM', 'PM'] ,
                closeButtonText: 'Zavřít',
                nowButtonText: 'Nyní',
                deselectButtonText: 'Odoznačit' }
    $.fgtimepicker.setDefaults($.fgtimepicker.regional['cs']);
});