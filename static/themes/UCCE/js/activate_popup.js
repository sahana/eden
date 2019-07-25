$(document).ready(function(){
    // Click-events for buttons
    $('#buttons').find('.button')
                 .off('click.ucce')
                 .on('click.ucce', function(event) {
        var $this = $(this);
        if ($this.hasClass('secondary')) {
            // Cancel: close Popup
            self.parent.S3.popup_remove();
        }
        if ($this.hasClass('disabled')) {
            event.preventDefault();
                return false;
        }
        return true
    });
    // Change events for checkboxes
    var checkbox1 = $('#checkbox1'),
        checkbox2 = $('#checkbox2');
    checkbox1.off('change.ucce')
             .on('change.ucce', function(event) {
        if (checkbox1.is(':checked') && checkbox2.is(':checked')) {
            $('.button.disabled').removeClass('disabled').addClass('alert');
        }
    });
    checkbox2.off('change.ucce')
             .on('change.ucce', function(event) {
        if (checkbox1.is(':checked') && checkbox2.is(':checked')) {
            $('.button.disabled').removeClass('disabled').addClass('alert');
        }
    });
});