(function($) {
    // Logic for forms
    function init_cap_form($form) {
        // On change in scope
        $form.find('[name=scope]').change(function() {
            var scope = $(this).val(),
                $restriction = $form.find('[name=restriction]'),
                $recipients  = $form.find('[name=addresses]'),

                disable = function (item) {
                            item.parents('tr').eq(0).hide().prev().hide();
                          } //XXX: hide or disable?
                enable  = function (item) {
                            item.parents('tr').eq(0).show().prev().show();
                          };
              console.log($restriction);
              console.log($recipients);

            switch(scope) {
                case "Public":
                    disable($restriction);
                    disable($recipients);
                    break;
                case "Restricted":
                    enable($restriction);
                    disable($recipients);
                    break;
                case "Private":
                    disable($restriction);
                    enable($recipients);
                    break;
            }
        });
    }

    $('form').each(function() {
        var _formname = $(this).find('[name=_formname]').val(),
            alert_form = 'cap_alert';
            console.log(_formname);
        if (_formname.substring(0, alert_form.length) == alert_form) {
            init_cap_form($(this));
        }
    });
})(jQuery, undefined);
