$(document).ready(function() {
    $('#nav').children('li').mouseenter(function() {
        $('#nav').find('.sub-menu:visible').hide();
        $(this).children('.sub-menu').show().one('mouseleave', function() {
            $(document).unbind('mousedown.rms');
            $(this).hide();
        }).each(function() {
            self = $(this);
            $(document).unbind('mousedown.rms').bind('mousedown.rms', function(event) {
                var target = event.target;
                if (!$.contains(self, target)) {
                    $(document).unbind('mousedown.rms');
                    self.hide();
                }
            });
        });
    });
});