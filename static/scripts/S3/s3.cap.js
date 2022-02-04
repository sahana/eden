(function($, JSON) {

    /**
     * Bind button event handlers for clone
     */
    var bindCloneActions = function() {
        $('.cap-clone-update').off('.cap').on('click.cap', function() {
            clone($(this).attr('data'));
        });
    };

    /**
     * Clone (Ajax)
     *
     * @param recordID - record ID for which clone is called
     * @param data - msgType/alert_id data
     */
    var clone = function(data) {
        var msgType = data.split('/')[0];
        var recordID = data.split('/').pop();
        if (recordID) {
            $.ajax({
                'url': S3.Ap.concat('/cap/alert/') + recordID + '/' + 'clone?msg_type=' + msgType,
                'success': function(data) {
                    window.location.href = S3.Ap.concat('/cap/alert/') + data['message'];
                },
                'error': function(request, status, error) {
                    if (error == 'UNAUTHORIZED') {
                        var msg = i18n.gis_requires_login;
                    } else {
                        var msg = request.responseText;
                    }
                    console.log(msg);
                },
                'type': 'POST',
                'dataType': 'json'
            });
        }
    };

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
            return ('codes,note,incidents').split(',');

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
        // Initialization of the cap_form
        var restriction_row = $('#cap_alert_restriction__row, #cap_alert_restriction__row1');
        var recipient_row = $('#cap_alert_addresses__row, #cap_alert_addresses__row1');
        // Show the restriction field if scope is restricted otherwise hide by default
        if ($('#cap_alert_scope').val() == 'Restricted') {
            restriction_row.show();
            recipient_row.hide();
        } else if($('#cap_alert_scope').val() == 'Public' || $('#cap_alert_scope').val() == 'Private') {
            recipient_row.show();
            restriction_row.hide();
        } else {
            recipient_row.hide();
            restriction_row.hide();
        }
        // On change in scope
        $('#cap_alert_scope').change(function() {
            var scope = $(this).val();
            switch(scope) {
                case 'Public':
                    restriction_row.hide();
                	if ($('#cap_alert_restriction').val()) {
                	    $('#cap_alert_restriction').val('');
                	}
                    recipient_row.show();
                    break;
                case 'Restricted':
                    recipient_row.hide();
                    if ($('#cap_alert_addresses').val()) {
                        $('#cap_alert_addresses').val('');
                    }
                    restriction_row.show();
                    break;
                case 'Private':
                    restriction_row.hide();
                	if ($('#cap_alert_restriction').val()) {
                	    $('#cap_alert_restriction').val('');	
                	}
                    recipient_row.show();
                    break;
                case '':
                    recipient_row.hide();
                    restriction_row.hide();
                    break;   
            }
        });

        $('#cap_info_priority').change(function() {
        	if (!$(this).val()) {
        	    $(this).css('border', '1px solid gray');
        	}
        	else {
	            var p = S3.cap_priorities,
	                len = p.length;
	            if ($(this).find('option:selected').text() == 'Undefined') {
	                $(this).css('border', '2px solid gray');
	                $form.find('[name=urgency]').val('');
	                $form.find('[name=severity]').val('');
	                $form.find('[name=certainty]').val('');
	            }
	            for (var i=0; i< len; i++) {
	                if (p[i][0] == $(this).find('option:selected').text()) {
	                    $form.find('[name=urgency]').val(p[i][1]);
	                    $form.find('[name=severity]').val(p[i][2]);
	                    $form.find('[name=certainty]').val(p[i][3]);
	                    $(this).css('border', '2px solid #' + p[i][4]);
	                }
	            }
	        }
        });

        /*$form.find('[name=urgency],[name=severity],[name=certainty]').change(function() {
            var p = S3.cap_priorities,
                len = p.length;
            for (var i=0; i< len; i++) {
                if ($form.find('[name=urgency]').val()   == p[i][1] &&
                    $form.find('[name=severity]').val()  == p[i][2] &&
                    $form.find('[name=certainty]').val() == p[i][3]) {
                        $('#cap_info_priority option').each(function() {
                            if($(this).text() == p[i][0]) {
                                $(this).prop('selected', 'selected');
                                $form.find('[name=priority]').css('border', '2px solid #' + p[i][4]);
                            } else {
                            	$form.find('[name=priority]').val('');
                            	$form.find('[name=priority]').css('border', '2px solid gray');
                              }                      
                        });
                    return;
                } else {
                	$form.find('[name=priority]').val('');
                    $form.find('[name=priority]').css('border', '2px solid gray');
                  }
            }

            $form.find('[name=priority]').val('Undefined')
                 .css('border', '2px solid gray');
        });*/

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
                //settings = $.parseJSON(values.template_settings) || {};
                // Note there is not template_settings in cap_info; kept this just to make API compatible and remove jQuery warning
                settings = {}
            }

            $.each(fields, function (i, f) {
                try {
                    var $f = $form.find('[name=' + f +']');
                    var locked = settings.locked && settings.locked[f];

                    switch(typeof(values[f])) {
                    case 'string':
                    	if (f == 'restriction') {
                    		$f.val(values[f] || '');
                    		if ($f.val() != '') {
                    			restriction_row.show();
                    		}
                    	} else {
                            recipient_row.show();
                            restriction_row.hide();
                        }
                    case 'undefined':
                        // change field only if locked or overwrite flag is set
                        if ($f.is(':text') || $f.is('textarea') || $f.is('select')) {
                            if (overwrite || locked) {
                                $f.val(values[f] || '');
                            }

                            if (locked) {
                                $f.prop('disabled', true)
                                  // @ToDo: i18n
                                  .attr('title', 'This field is locked by the template');
                            } else {
                                $f.prop('disabled', false)
                                  .attr('title', '');
                            }
                        }
                        break;
                    case 'object':
                    	var prop = ['scope', 'addresses', 'codes'];
                    	for (var i = 0; i < prop.length; i++) {
                    		if (f == prop[i]) {
                    			$f.val(values[f]['@value'] || '');
                    		}
                    	}

                        if (f == 'incidents') {
                            if (overwrite || locked) {
                                $f.val(values[f]['@value'] || '');
                                //refresh multiselect widget for display
                                $('select#cap_alert_incidents').multiselect('refresh');
                            }                                                
                        } else {
                            break;
                        }
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
            apply_alert_template($form.find('[name=template_id]').val());
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
        $form.find('[name=is_template]').prop('checked', 'checked');

        function inheritable_flag(field, $e) {
            var name = 'can_edit-' + field,
                $label = $('<label for="' + name + '">' +
                                (i18n.cap_locked || 'Locked') + '</label>'),
                $checkbox = $('<input type="checkbox" name="' + name +'"/>');

            $checkbox.change(function () {
                var settings = get_settings();
                settings.locked = settings.locked || {};
                settings.locked[field] = $(this).is(':checked');
                set_settings(settings);
            });

            var settings = get_settings();
            if (settings.locked && settings.locked[field]) {
                $checkbox.prop('checked', 'checked');
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
            if (get_table($(this)) !== '') {
                init_cap_form($(this));
                if (is_cap_template() || is_cap_info_template()) {
                    init_template_form($(this));
                }
            }
        });
        // bind at document-ready
        bindCloneActions();
    });
})(jQuery, JSON, undefined);
