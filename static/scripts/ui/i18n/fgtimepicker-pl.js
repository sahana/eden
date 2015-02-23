/* Polish initialisation for the timepicker plugin */
/* Written by Mateusz Wadolkowski (mw@pcdoctor.pl). */
jQuery(function($){
    $.fgtimepicker.regional['pl'] = {
                hourText: 'Godziny',
                minuteText: 'Minuty',
                amPmText: ['', ''],
				closeButtonText: 'Zamknij',
                nowButtonText: 'Teraz',
                deselectButtonText: 'Odznacz'}
    $.fgtimepicker.setDefaults($.fgtimepicker.regional['pl']);
});