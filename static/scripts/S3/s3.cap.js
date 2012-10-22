(function($, JSON) {

    function get_table($form) {
        var _formname = $form.find('[name=_formname]').val();
        var alert_table = 'cap_alert';
        var info_table = 'cap_info';

        if (typeof(_formname) != 'undefined') {
            if (_formname.substring(0, alert_table.length) == alert_table) {
                return alert_table;
            }
            if (_formname.substring(0, info_table.length) == info_table) {
                return info_table;
            }
        }
        return '';
    }

    function is_cap_template() {
        return $('.cap_template_form').length > 0;
    }

    function is_cap_info_template() {
        return $('.cap_info_template_form').length > 0;
    }

    function get_template_fields(table) {
        if (table == 'cap_alert') {
            return ('sender,sent,status,msg_type,source,scope,' +
                    'restriction,addresses,codes,note,reference,' +
                    'incidents').split(',');

        } else if (table == 'cap_info') {
             return ('category,event,response_type,urgency,' +
                     'severity,certainty,audience,event_code,' +
                     'effective,onset,expires,sender_name,headline,' +
                     'description,instruction,contact,web,parameter').split(',');
        }
        return [];
    }
    window.fields = get_template_fields;

    // Logic for forms
    function init_cap_form($form) {
        // On change in scope
        $form.find('[name=scope]').change(function() {
            var scope = $(this).val(),
                $restriction = $form.find('[name=restriction]'),
                $recipients  = $form.find('[name=addresses]'),

                disable = function (item) {
                            item.parents('tr').eq(0).hide().prev().hide();
                          } // @ToDo: hide or disable?
                enable  = function (item) {
                            item.parents('tr').eq(0).show().prev().show();
                          };

            switch(scope) {
                case 'Public':
                    disable($restriction);
                    disable($recipients);
                    break;
                case 'Restricted':
                    enable($restriction);
                    disable($recipients);
                    break;
                case 'Private':
                    disable($restriction);
                    enable($recipients);
                    break;
            }
        });

        $form.find('[name=priority]').change(function() {
            var p = S3.cap_priorities,
                len = p.length;
            if ($(this).val() == 'Undefined') {
                $(this).css('border', '2px solid gray');
                $form.find('[name=urgency]').val('');
                $form.find('[name=severity]').val('');
                $form.find('[name=certainty]').val('');
            }
            for (var i=0; i< len; i++) {
                if (p[i][0] == $(this).val()) {
                    $form.find('[name=urgency]').val(p[i][1]);
                    $form.find('[name=severity]').val(p[i][2]);
                    $form.find('[name=certainty]').val(p[i][3]);
                    $(this).css('border', '2px solid ' + p[i][4]);
                }
            }
        });

        $form.find('[name=urgency],[name=severity],[name=certainty]').change(function() {
            var p = S3.cap_priorities,
                len = p.length;
            for (var i=0; i< len; i++) {
                if ($form.find('[name=urgency]').val()   == p[i][1] &&
                    $form.find('[name=severity]').val()  == p[i][2] &&
                    $form.find('[name=certainty]').val() == p[i][3]) {
                    $form.find('[name=priority]').val(p[i][0])
                         .css('border', '2px solid ' + p[i][4]);
                    return;
                }
            }

            $form.find('[name=priority]').val('Undefined')
                 .css('border', '2px solid gray');
        });

        function load_template_data(data, overwrite) {
            var tablename = get_table($form),
                fields = get_template_fields(tablename),
                values, settings = {};

            if (typeof(overwrite) == 'undefined') {
                overwrite = false;
            }

            if (!data) {
                values = {};
                settings = {};
            } else if (tablename == 'cap_alert') {
                values = (data['$_cap_alert'] && data['$_cap_alert'][0]) || {};
                settings = $.parseJSON(values.template_settings) || {};
                $('.cap_alert_form').addClass('template_loaded');
            } else if (tablename == 'cap_info') {
                values = (data['$_cap_info'] && data['$_cap_info'][0]) || {};
                settings = $.parseJSON(values.template_settings) || {};
            }

            $.each(fields, function (i, f) {
                try {
                    var $f = $form.find('[name=' + f +']')
                    var locked = settings.locked && settings.locked[f];

                    switch(typeof(values[f])) {
                    case 'string':
                    case 'undefined':
                        // change field only if locked or overwrite flag is set
                        if ($f.is(':text') || $f.is('textarea') || $f.is('select')) {
                            if (overwrite || locked) {
                                $f.val(values[f] || '');
                            }

                            if (locked) {
                                $f.attr('disabled', true)
                                  // @ToDo: i18n
                                  .attr('title', 'This field is locked by the template');
                            } else {
                                $f.removeAttr('disabled')
                                  .attr('title', '');
                            }
                        }
                        break;
                    case 'object':
                        break;
                    }
                } catch(e) {
                    s3_debug('ERROR', e);
                }
            });
        }

        function apply_alert_template(id, overwrite, type) {
            if (!id) return;

            if (typeof(type) == 'undefined') {
                type = 'template';
            }

            var re = new RegExp('.*\\' + S3.Ap + '\\/'),
                _url = new String(self.location),
                module = _url.replace(re, '').split('?')[0].split('/')[0],
                url = [S3.Ap, module, type, id].join('/') + '.s3json';

            $.ajax({
                url: url,
                type: 'GET',
                dataType: 'json',
                success: function(data) {
                    load_template_data(data, overwrite);
                },
                error: function(e) {
                    // @ToDo: i18n
                    alert('There was an unexpected error loading template data');
                }
            });
        }

        $form.find('[name=template_id]').change(function () {
            apply_alert_template($(this).val(), true);
        });

        if (get_table($form) == 'cap_alert' && !is_cap_template()) {
            apply_alert_template($form.find('[name=template_id]').val())
        }

        if (get_table($form) == 'cap_info' && !is_cap_info_template()) {
            apply_alert_template($form.find('[name=template_info_id]').val(), false, 'info');
        }

        window.apply_temp = apply_alert_template;
    }

    function init_template_form($form) {

        /* Templates-specific stuff */
        function get_settings() {
            try {
                var settings = $.parseJSON($form.find('[name=template_settings]').val());
                return settings || {};
            } catch (e) {
                s3_debug('Error occured parsing: ', $form.find('[name=template_settings]').val());
                return {};
            }
        }

        function set_settings(settings) {
            $form.find('[name=template_settings]').val(JSON.stringify(settings));
        }

        // Set as template
        $form.find('[name=is_template]').attr('checked', 'checked');

        function inheritable_flag(field, $e) {
            var name = 'can_edit-' + field,
                $label = $('<label for="' + name + '">' +
                                (S3.i18n.cap_locked || 'Locked') + '</label>'),
                $checkbox = $('<input type="checkbox" name="' + name +'"/>');

            $checkbox.change(function () {
                var settings = get_settings();
                settings.locked = settings.locked || {};
                settings.locked[field] = $(this).is(':checked');
                set_settings(settings);
            });

            var settings = get_settings();
            if (settings.locked && settings.locked[field]) {
                $checkbox.attr('checked', 'checked');
            }

            $e.append($label);
            $e.append($checkbox);
        }

        tablename = get_table($form);
        fields = get_template_fields(tablename);

        $form.find('tr').each(function () {
            var $tr = $(this);
            var id = $tr.attr('id');

            if (id && id.match('__row$')) {
                // this row contains the field and comment
                var name = id.replace(tablename + '_', '').replace('__row', ''),
                    $comment = $tr.find('td.w2p_fc') || $tr.find('td').eq(1);
                if (fields.indexOf(name) >= 0) {
                    inheritable_flag(name, $comment);
                }
            }
        });
    }

    $(document).ready(function() {
        $('form').each(function() {
            if (get_table($(this)) != '') {
                init_cap_form($(this));
                if (is_cap_template() || is_cap_info_template()) {
                    init_template_form($(this));
                }
            }
        });
    });
})(jQuery, JSON, undefined);
