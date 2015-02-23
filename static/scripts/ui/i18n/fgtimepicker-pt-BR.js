/* Brazilan initialisation for the timepicker plugin */
/* Written by Daniel Almeida (quantodaniel@gmail.com). */
jQuery(function($){
    $.fgtimepicker.regional['pt-BR'] = {
                hourText: 'Hora',
                minuteText: 'Minuto',
                amPmText: ['AM', 'PM'],
                closeButtonText: 'Fechar',
                nowButtonText: 'Agora',
                deselectButtonText: 'Limpar' }
    $.fgtimepicker.setDefaults($.fgtimepicker.regional['pt-BR']);
});