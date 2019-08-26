$(document).ready(function(){
    // Click-events for buttons
    $('#buttons').find('.button')
                 .off('click.ucce')
                 .on('click.ucce', function(event) {
        var $this = $(this);
        if ($this.hasClass('secondary')) {
            // Cancel: close Popup
            window.parent.S3.popup_remove();
        } else if ($this.hasClass('disabled')) {
            event.preventDefault();
                return false;
        }
        return true;
    });
    // Change events for checkboxes
    var checkboxes = $('#checkbox1, #checkbox2');
    checkboxes.off('.ucce')
              .on('change.ucce', function() {
        if (checkboxes.not(':checked').length == 0) {
            $('.button.disabled').removeClass('disabled');
        }
    });
});
