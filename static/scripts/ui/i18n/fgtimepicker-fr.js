/* French initialisation for the jQuery time picker plugin. */
/* Written by Bernd Plagge (bplagge@choicenet.ne.jp),
              Francois Gelinas (frank@fgelinas.com) */
jQuery(function($){
    $.fgtimepicker.regional['fr'] = {
                hourText: 'Heures',
                minuteText: 'Minutes',
                amPmText: ['AM', 'PM'],
                closeButtonText: 'Fermer',
                nowButtonText: 'Maintenant',
                deselectButtonText: 'Désélectionner' }
    $.fgtimepicker.setDefaults($.fgtimepicker.regional['fr']);
});