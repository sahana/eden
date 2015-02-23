/* Croatian/Bosnian initialisation for the timepicker plugin */
/* Written by Rene Brakus (rene.brakus@infobip.com). */
jQuery(function($){
    $.fgtimepicker.regional['hr'] = {
                hourText: 'Sat',
                minuteText: 'Minuta',
                amPmText: ['Prijepodne', 'Poslijepodne'],
                closeButtonText: 'Zatvoriti',
                nowButtonText: 'Sada',
                deselectButtonText: 'Poništite'}

    $.fgtimepicker.setDefaults($.fgtimepicker.regional['hr']);
});