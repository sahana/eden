/**
 * Custom Javascript functions added as part of the S3 Framework
 * Strings are localised in views/l10n.js
 */

 /**
 * The startsWith string function is introduced in JS 1.8.6 -- it's not even
 * accepted in ECMAScript yet, so don't expect all browsers to have it.
 * Thx to http://www.moreofless.co.uk/javascript-string-startswith-endswith/
 * for showing how to add it to string if not present.
 */
if (typeof String.prototype.startsWith != 'function') {
    String.prototype.startsWith = function(str) {
        return this.substring(0, str.length) === str;
    };
}

// Global variable to store all of our variables inside
var S3 = Object();
S3.gis = Object();
S3.gis.options = Object();
S3.timeline = Object();
S3.JSONRequest = Object(); // Used to store and abort JSON requests
//S3.TimeoutVar = Object(); // Used to store and abort JSON requests

S3.queryString = {
    // From https://github.com/sindresorhus/query-string
	parse: function(str) {
		if (typeof str !== 'string') {
			return {};
		}

		str = str.trim().replace(/^(\?|#)/, '');

		if (!str) {
			return {};
		}

		return str.trim().split('&').reduce(function (ret, param) {
			var parts = param.replace(/\+/g, ' ').split('=');
			var key = parts[0];
			var val = parts[1];

			key = decodeURIComponent(key);
			// missing `=` should be `null`:
			// http://w3.org/TR/2012/WD-url-20120524/#collect-url-parameters
			val = val === undefined ? null : decodeURIComponent(val);

			if (!ret.hasOwnProperty(key)) {
				ret[key] = val;
			} else if (Array.isArray(ret[key])) {
				ret[key].push(val);
			} else {
				ret[key] = [ret[key], val];
			}

			return ret;
		}, {});
	},
	stringify: function(obj) {
		return obj ? Object.keys(obj).map(function (key) {
			var val = obj[key];

			if (Array.isArray(val)) {
				return val.map(function (val2) {
					return encodeURIComponent(key) + '=' + encodeURIComponent(val2);
				}).join('&');
			}

			return encodeURIComponent(key) + '=' + encodeURIComponent(val);
		}).join('&') : '';
	}
};

S3.uid = function() {
    // Generate a random uid
    // Used for jQueryUI modals and some Map popups
    // http://jsperf.com/random-uuid/2
    return (((+(new Date())) / 1000 * 0x10000 + Math.random() * 0xffff) >> 0).toString(16);
};

S3.Utf8 = {
    // Used by dataTables
    // http://www.webtoolkit.info
    encode: function(string) {
        string = string.replace(/\r\n/g, '\n');
        var utftext = '';
        for (var n = 0; n < string.length; n++) {
            var c = string.charCodeAt(n);
            if (c < 128) {
                utftext += String.fromCharCode(c);
            } else if ((c > 127) && (c < 2048)) {
                utftext += String.fromCharCode((c >> 6) | 192);
                utftext += String.fromCharCode((c & 63) | 128);
            } else {
                utftext += String.fromCharCode((c >> 12) | 224);
                utftext += String.fromCharCode(((c >> 6) & 63) | 128);
                utftext += String.fromCharCode((c & 63) | 128);
            }
        }
        return utftext;
    },
    decode: function(utftext) {
        var string = '';
        var i = 0;
        var c1, c2;
        var c = c1 = c2 = 0;
        while ( i < utftext.length ) {
            c = utftext.charCodeAt(i);
            if (c < 128) {
                string += String.fromCharCode(c);
                i++;
            } else if ((c > 191) && (c < 224)) {
                c2 = utftext.charCodeAt(i+1);
                string += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
                i += 2;
            } else {
                c2 = utftext.charCodeAt(i+1);
                c3 = utftext.charCodeAt(i+2);
                string += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
                i += 3;
            }
        }
        return string;
    }
};

S3.addTooltips = function() {
    // Help Tooltips
    $.cluetip.defaults.cluezIndex = 9999; // Need to be able to show on top of Ext Windows
    $('.tooltip').cluetip({activation: 'hover', sticky: false, splitTitle: '|'});
    $('label[title]').cluetip({splitTitle: '|', showTitle:false});
    $('.tooltipbody').cluetip({activation: 'hover', sticky: false, splitTitle: '|', showTitle: false});
    var tipCloseText = '<img src="' + S3.Ap.concat('/static/img/cross2.png') + '" alt="close" />';
    $('.stickytip').cluetip({
    	activation: 'hover',
    	sticky: true,
    	closePosition: 'title',
    	closeText: tipCloseText,
    	splitTitle: '|'
    });
    $('.errortip').cluetip({
        activation: 'click',
        sticky: true,
        closePosition: 'title',
        closeText: tipCloseText,
        splitTitle: '|'
    });
    $('.ajaxtip').cluetip({
    	activation: 'click',
    	sticky: true,
    	closePosition: 'title',
    	closeText: tipCloseText,
    	width: 380
    });
};

// jQueryUI Modal Popups
S3.addModals = function() {
    $('a.s3_add_resource_link').attr('href', function(index, attr) {
        var url_out = attr;
        // Avoid Duplicate callers
        if (attr.indexOf('caller=') == -1) {
            // Add the caller to the URL vars so that the popup knows which field to refresh/set
            // Default formstyle
            var caller = $(this).parents('tr').attr('id');
            if (!caller) {
                // DIV-based formstyle
                caller = $(this).parent().parent().attr('id');
            }
            if (!caller) {
                caller = $(this).parents('.form-row').attr('id');
            }
            if (!caller) {
                // Bootstrap formstyle
                caller = $(this).parents('.control-group').attr('id');
            }
            if (caller) {
                caller = caller.replace(/__row_comment/, '') // DRRPP formstyle
                               .replace(/__row/, '');
                url_out = attr + '&caller=' + caller;
            }
        }
        return url_out;
    });
    $('.s3_add_resource_link, .s3_modal').unbind('click.S3Modal')
                                         .on('click.S3Modal', function() {
        var title = this.title;
        var url = this.href;
        var i = url.indexOf('caller=');
        if (i != -1) {
            var caller = url.slice(i + 7);
            i = caller.indexOf('&');
            if (i != -1) {
                caller = caller.slice(0, i);
            }
            var select = $('#' + caller);
            if (select.hasClass('multiselect-widget')) {
                // Close the menu (otherwise this shows above the popup)
                select.multiselect('close');
                // Lower the z-Index
                //select.css('z-index', 1049);
            }
        }
        var id = S3.uid();
        // Open a jQueryUI Dialog showing a spinner until iframe is loaded
        var dialog = $('<iframe id="' + id + '" src=' + url + ' onload="S3.popup_loaded(\'' + id + '\')" class="loading" marginWidth="0" marginHeight="0" frameBorder="0"></iframe>')
                      .appendTo('body');
        dialog.dialog({
            // add a close listener to prevent adding multiple divs to the document
            close: function(event, ui) {
                if (self.parent) {
                    // There is a parent modal: refresh it to fix layout
                    var iframe = self.parent.$('iframe.ui-dialog-content');
                    var width = iframe.width();
                    iframe.width(0);
                    window.setTimeout(function() {
                        iframe.width(width);
                    }, 300);
                }
                // remove div with all data and events
                dialog.remove();
            },
            minHeight: 480,
            modal: true,
            open: function(event, ui) {
                $('.ui-widget-overlay').bind('click', function() {
                    dialog.dialog('close');
                });
            },
            title: title,
            minWidth: 320,
            closeText: ''
        });
        // Prevent browser from following link
        return false;
    });
};
S3.popup_loaded = function(id) {
    // Resize the iframe to fit the Dialog
    // If we need to support multiple per-frame, can identify uniquely via:
    //$(".ui-dialog[aria-describedby='" + id + "']").width();
    if (window != window.parent) {
        // Popup inside Popup: increase size of parent popup
        // 41 is the size of the .ui-dialog-titlebar
        // @ToDo: handle parent of parent
        var parent_dialog = $(window.parent.document).find('.ui-dialog');
        var parent_height = parent_dialog.height();
        parent_dialog.height(parent_height + 41);
        var parent_iframe = parent_dialog.find('iframe');
        var parent_iframe_height = parent_iframe.height();
        parent_iframe.height(parent_iframe_height + 41);
    }
    var width = $('.ui-dialog').width();
    $('#' + id).width(width)
               // Display the hidden form
               .contents().find('#popup form').show();
};
S3.popup_remove = function() {
    // Close jQueryUI Dialog Modal Popup
    // - called from s3.popup.js but in parent scope
    $('iframe.ui-dialog-content').dialog('close');
};

// Functions to re-run after new page elements are brought in via AJAX
// - an be added-to dynamically
S3.redraw_fns = [// jQueryUI Dialog Modal Popups
                 'addModals',
                 // Help Tooltips
                 'addTooltips'
                 ];
S3.redraw = function() {
    var redraw_fns = S3.redraw_fns;
    var len = redraw_fns.length;
    for (var i=0; i < len; i++) {
        S3[redraw_fns[i]]();
    }
};

// jQueryUI Icon Menus
// - http://jqueryui.com/selectmenu/#custom_render
// - used by S3SelectWidget()
$.widget('custom.iconselectmenu', $.ui.selectmenu, {
    _renderItem: function(ul, item) {
        var li = $('<li>', {text: item.label} );
 
        if (item.disabled) {
            li.addClass('ui-state-disabled');
        }
 
        var element = item.element;
        var _class = item.element.attr('data-class');
        if (_class) {
            _class = 'ui-icon ' + _class;
        } else {
            _class = 'ui-icon';
        }
        $('<span>', {
            'style': element.attr('data-style'),
            'class': _class
        })
          .appendTo(li);
 
        return li.appendTo(ul);
    }
});

// Geolocation
// - called from Auth.login()
S3.getClientLocation = function(targetfield) {
   if (navigator.geolocation) {
    	navigator.geolocation.getCurrentPosition(function(position) {
			var clientlocation = position.coords.latitude + '|' + position.coords.longitude + '|' + position.coords.accuracy;
			targetfield.val(clientlocation);
    	});
    }
};

// ============================================================================
S3.confirmClick = function(ElementID, Message) {
	// @param ElementID: the ID of the element which will be clicked
	// @param Message: the Message displayed in the confirm dialog
	if (S3.interactive) {
        $(ElementID).click( function(event) {
            if (confirm(Message)) {
                return true;
            } else {
                event.preventDefault();
                return false;
            }
        });
    }
};

// ============================================================================
S3.trunk8 = function(selector, lines, more) {
    // Line-truncation, see s3utils.s3_trunk8
    var settings = {
        fill: '&hellip; <a class="s3-truncate-more" href="#">' + more + '</a>'
    };
    if (lines) {
        settings['lines'] = lines;
    }
    $(selector).trunk8(settings);
    // Attach to any new items after Ajax-listUpdate (dataLists)
    $('.dl').on('listUpdate', function() {
        $(this).find(selector).each(function() {
            if (this.trunk8 === undefined) {
                $(this).trunk8(settings);
            }
        });
    });
};

// ============================================================================
// Limit the size of a textbox dynamically
S3.maxLength = {
    init: function(id, maxLength) {
        var apply = this.apply;
        if (maxLength) {
            var input = $('#' + id);
            input.next('div.maxLength_status').remove();
            input.after('<div class="maxLength_status"></div>');
            // Apply current settings
            apply(id, maxLength);
            input.unbind('keyup.maxLength')
                 .bind('keyup.maxLength', function(evt) {
                // Apply new settings
                apply(id, maxLength);
            });
        } else {
            // Remove the limits & cleanup
            $('#' + id).removeClass('maxLength')
                       .unbind('keyup.maxLength')
                       .next('div.maxLength_status').remove();
        }
    },

    apply: function(id, maxLength) {
        message = i18n.characters_left || 'characters left';
        var input = $('#' + id);
        var currentLength = input.val().length;
        if (currentLength >= maxLength) {
            // Add the notification class
            input.addClass('maxLength');
            // Cut down the string
            input.val(input.val().substr(0, maxLength));
        } else {
            // Remove the notification class
            input.removeClass('maxLength');
        }
        var remaining = maxLength - currentLength;
        if (remaining < 0) {
            remaining = 0;
        }
        input.next('div.maxLength_status').html(remaining + ' ' + message);
    }
};

// ============================================================================
// Code to warn on exit without saving
var S3SetNavigateAwayConfirm = function() {
    window.onbeforeunload = function() {
        return i18n.unsaved_changes;
    };
};

var S3ClearNavigateAwayConfirm = function() {
    window.onbeforeunload = function() {};
};

var S3EnableNavigateAwayConfirm = function() {
    $(document).ready(function() {
        if ($('[class=error]').length > 0) {
            // If there are errors, ensure the unsaved form is still protected
            S3SetNavigateAwayConfirm();
        }
        var form = 'form:not(form.filter-form)',
            input = 'input:not(input[id=gis_location_advanced_checkbox])',
            select = 'select';
        $(form + ' ' + input).keypress(S3SetNavigateAwayConfirm);
        $(form + ' ' + input).change(S3SetNavigateAwayConfirm);
        $(form + ' ' + select).change(S3SetNavigateAwayConfirm);
        $('form').submit(S3ClearNavigateAwayConfirm);
    });
};

// ============================================================================
/**
 * ajaxS3
 * - wrapper for jQuery AJAX to handle poor network environments
 * - retries failed requests & alerts on errors
 */

(function($) {
    // Default AJAX settings
    $.ajaxS3Settings = {
        timeout : 10000,
        //msgTimeout: 2000,
        retryLimit: 5,
        dataType: 'json',
        async: true,
        type: 'GET'
    };

    $.ajaxS3 = function(s) {
        var message;
        var options = $.extend( {}, $.ajaxS3Settings, s );
        options.tryCount = 0;
        options.error = null;   // prevent callback from being executed twice
        options.success = null; // prevent callback from being executed twice
        if (s.message) {
            message = i18n.ajax_get + ' ' + (s.message ? s.message : i18n.ajax_fmd) + '...';
            S3.showAlert(message, 'info');
        }
        $.ajax(
            options
        ).done(function(data, status) {
            S3.hideAlerts();
            this.tryCount = 0;
            if (data.message) {
                S3.showAlert(data.message, 'success');
            }
            // @ToDo: support drop-in replacement functions by calling .done()
            if (s.success) {
                // Calling function's success callback
                s.success(data, status);
            }
        }).fail(function(jqXHR, textStatus, errorThrown) {
            if (textStatus == 'timeout') {
                this.tryCount++;
                if (this.tryCount <= this.retryLimit) {
                    // Try again
                    message = i18n.ajax_get + ' ' + (s.message ? s.message : i18n.ajax_fmd) + '... ' + i18n.ajax_rtr + ' ' + this.tryCount;
                    S3.showAlert(message, 'warning');
                    $.ajax(this);
                    return;
                }
                message = i18n.ajax_wht + ' ' + (this.retryLimit + 1) + ' ' + i18n.ajax_gvn;
                S3.showAlert(message, 'error');
                if (s.error) {
                    // Calling function's error callback
                    s.error(jqXHR, textStatus, errorThrown);
                }
                return;
            }
            if (jqXHR.status == 500) {
                // @ToDo: Can we find & show the ticket URL?
                S3.showAlert(i18n.ajax_500, 'error');
            } else {
                S3.showAlert(i18n.ajax_dwn, 'error');
            }
            if (s.error) {
                // Calling function's error callback
                s.error(jqXHR, textStatus, errorThrown);
            }
        });
    };

    // Simplified wrappers for .ajaxS3
    $.getS3 = function(url, data, callback, type, message, sync) {
        // shift arguments if data argument was omitted
        if ( $.isFunction(data) ) {
            sync = message;
            message = type;
            type = callback;
            callback = data;
            data = null;
        }
        if (sync) {
            var async = false;
        }
        return $.ajaxS3({
            type: 'GET',
            url: url,
            async: async,
            data: data,
            dataType: type,
            message: message,
            // gets moved to .done() inside .ajaxS3
            success: callback
        });
    };

    $.getJSONS3 = function(url, data, callback, message, sync) {
        // shift arguments if data argument was omitted
        if ( $.isFunction(data) ) {
            sync = message;
            message = callback;
            callback = data;
            data = null;
        }
        if (!sync) {
            sync = false;
        }
        return $.getS3(url, data, callback, 'json', message, sync);
    };

})($);

/**
 * Display Status in Alerts section
 *
 *  To display an alert:
 *  S3.showAlert(message, type)
 *    message - string - message to display
 *    type    - string - alert type: 'error', 'info', 'success', 'warning'
 *
 *  To hide alerts:
 *  S3.hideAlerts()
 */
S3.showAlert = function(message, type) {
    if (undefined == type) {
        type = 'success';
    }
    var alert = '<div class="alert alert-' + type + '">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>';
    $('#alert-space').append(alert);
    $('.alert-' + type).click(function() {
        $(this).fadeOut('slow');
        return false;
    });
};

S3.hideAlerts = function(type) {
    if (type) {
        $('.alert-' + type).remove();
    } else {
        $('#alert-space').empty();
    }
};

/**
 * Display an Error next to a Field
 *
 *  To display an alert:
 *  S3.fieldError(selector, error)
 *    selector - string - selector for the field to display the error against
 *    error - string - message to display
 */
S3.fieldError = function(selector, error) {
    // @ToDo: Are we using a Bootstrap or normal Theme?
    // Display the Error
    $(selector).after('<div class="error" style="display: block;">' + error + '</div>');
};

S3.unmask = function(table, field) {
    // Toggle between * and readable characters
    var caller = table + '_' + field + '_' + 'unmask';
    var target = table + '_' + field;
    var state = $('#' + caller).text();
    if (state == i18n.password_view) {
        // Unmask the password
        state = i18n.password_mask;
        $('#' + target).attr('type', 'text');
        $('#' + caller).text(state);
    }
    else {
        // Mask the password
        state = i18n.password_view;
        $('#' + target).attr('type', 'password');
        $('#' + caller).text(state);
    }
};
// ============================================================================
var s3_viewMap = function(feature_id) {
    // Display a Feature on a BaseMap within an iframe
    var url = S3.Ap.concat('/gis/display_feature/') + feature_id;
    var oldhtml = $('#map').html();
    var iframe = "<iframe width='640' height='480' src='" + url + "'></iframe>";
    var closelink = $('<a href=\"#\">' + i18n.close_map + '</a>');

    // @ToDo: Also make the represent link act as a close
    closelink.bind('click', function(evt) {
        $('#map').html(oldhtml);
        evt.preventDefault();
    });

    $('#map').html(iframe);
    $('#map').append($("<div style='margin-bottom:10px' />").append(closelink));
};
var s3_viewMapMulti = function(module, resource, instance, jresource) {
    // Display a set of Features on a BaseMap within an iframe
    var url = S3.Ap.concat('/gis/display_feature//?module=') + module + '&resource=' + resource + '&instance=' + instance + '&jresource=' + jresource;
    var oldhtml = $('#map').html();
    var iframe = '<iframe width="640" height="480" src="' + url + '"></iframe>';
    var closelink = $('<a href=\"#\">' + i18n.close_map + '</a>');

    // @ToDo: Also make the represent link act as a close
    closelink.bind('click', function(evt) {
        $('#map').html(oldhtml);
        evt.preventDefault();
    });

    $('#map').html(iframe);
    $('#map').append($("<div style='margin-bottom:10px' />").append(closelink));
};
S3.popupWin = null;
S3.openPopup = function(url, center) {
    if ( !S3.popupWin || S3.popupWin.closed ) {
        var params = 'width=640, height=480';
        if (center === true) {
            params += ',left=' + (screen.width - 640)/2 +
                ',top=' + (screen.height - 480)/2;
        }
        S3.popupWin = window.open(url, 'popupWin', params);
    } else S3.popupWin.focus();
};
var s3_showMap = function(feature_id) {
    // Display a Feature on a BaseMap within an iframe
    var url = S3.Ap.concat('/gis/display_feature/') + feature_id;
	// new Ext.Window({
		// autoWidth: true,
		// floating: true,
		// items: [{
			// xtype: 'component',
			// autoEl: {
				// tag: 'iframe',
				// width: 650,
				// height: 490,
				// src: url
			// }
		// }]
	// }).show();
    S3.openPopup(url, true);
};

// ============================================================================
/**
 * Filter options of a drop-down field (=target) by the selection made
 * in another field (=trigger), e.g.:
 *   - Task Form: Activity options filtered by Project selection
 *
 * @todo: fix updateAddResourceLink
 * @todo: move into separate file and load only when needed?
 * @todo: S3SQLInlineComponentCheckboxes not supported (but to be
 *        deprecated itself anyway, so just remove the case?)
 */

(function() {

    /**
     * Get a CSS selector for trigger/target fields
     *
     * @param {string|object} setting - the setting for trigger/target, value of the
     *                                  name-attribute in regular form fields, or an
     *                                  object describing a field in an inline component
     *                                  (see below for the latter)
     * @param {string} setting.prefix - the inline form prefix (default: 'default')
     * @param {string} setting.alias - the component alias for the inline form (e.g. task_project)
     * @param {string} setting.name - the field name
     * @param {string} setting.inlineType - the inline form type, 'link' (for S3SQLInlineLink),
     *                                      or 'sub' (for other S3SQLInlineComponent types)
     * @param {string} setting.inlineRows - the inline form has multiple rows, default: true,
     *                                      should be set to false for e.g.
     *                                      S3SQLInlineComponentMultiSelectWidget
     */
    var getSelector = function(setting) {

        var selector;
        if (typeof setting == 'string') {
            // Simple field name
            selector = '[name="' + setting + '"]';
        } else {
            // Inline form
            var prefix = setting.prefix ? setting.prefix : 'default';
            if (setting.alias) {
                prefix += setting.alias;
            }
            var type = setting.inlineType || 'sub',
                rows = setting.inlineRows || true;
            if (type == 'sub') {
                var name = setting.name;
                if (rows) {
                    selector = '[name^="' + prefix + '"][name*="_i_' + name + '_edit_"]';
                } else {
                    selector = '[name="' + prefix + '-' + name + '"]';
                }
            } else if (type == 'link') {
                selector = '[name="link_' + prefix + '"]';
            }
        }
        return selector;
    };


    /**
     * Add a throbber while loading the widget options
     *
     * @param {object} widget - the target widget
     * @param {string} resourceName - the target resource name
     */
    var addThrobber = function(widget, resourceName) {

        var throbber = widget.siblings('.' + resourceName + '-throbber');
        if (!throbber.length) {
            widget.after('<div class="' + resourceName + '-throbber throbber"/>');
        }
    };

    /**
     * Remove a previously inserted throbber
     *
     * @param {string} resourceName - the target resource name
     */
    var removeThrobber = function(widget, resourceName) {

        var throbber = widget.siblings('.' + resourceName + '-throbber');
        if (throbber.length) {
            throbber.remove();
        }
    };

    /**
     * Update the AddResourceLink for the lookup resource with the lookup value
     *
     * @todo: rename resource => resourceName or lookupResource
     * @todo: docstring
     */
    var updateAddResourceLink = function(resource, key, value) {

        var addResourceLink = $('#' + resource + '_add');
        if (addResourceLink.length) {
            var href = addResourceLink.attr('href');
            if (href.indexOf(key) == -1) {
                // Add to URL
                // @todo: make safe for URLs without query part
                href += '&' + key + '=' + value;
            } else {
                // Update URL
                // @todo: make safe for URLs with multiple query expressions
                var re = new RegExp(key + '=.*', 'g');
                href = href.replace(re, key + '=' + value);
            }
            addResourceLink.attr('href', href).show();
        }
    };

    /**
     * Render the options from the JSON data
     *
     * @param {array} data - the JSON data
     * @param {object} settings - the settings
     */
    var renderOptions = function(data, settings) {

        var options = [],
            defaultValue = 0;

        if (data.length === 0) {
            // No options available
            var showEmptyField = settings.showEmptyField;
            if (showEmptyField || showEmptyField === undefined) {
                var msgNoRecords = settings.msgNoRecords || '-';
                options.push('<option value="">' + msgNoRecords + '</option>');
            }
        } else {

            // Pre-process the data
            var fncPrep = settings.fncPrep,
                prepResult = null;
            if (fncPrep) {
                try {
                    prepResult = fncPrep(data);
                } catch (e) {}
            }

            // Render the options
            var lookupField = settings.lookupField || 'id',
                fncRepresent = settings.fncRepresent,
                record,
                value,
                name;

            for (var i = 0; i < data.length; i++) {
                record = data[i];
                value = record[lookupField];
                if (i === 0) {
                    defaultValue = value;
                }
                name = fncRepresent ? fncRepresent(record, prepResult) : record.name;
                // Does the option have an onhover-tooltip?
                if (record._tooltip) {
                    title = ' title="' + record._tooltip + '"';
                } else {
                    title = ''
                }
                options.push('<option' + title + ' value="' + value + '">' + name + '</option>');
            }
            if (settings.optional) {
                // Add (and default to) empty option
                defaultValue = 0;
                options.unshift('<option value=""></option>');
            }
        }
        return {options: options.join(''), defaultValue: defaultValue};
    };

    /**
     * Update the options of the target field from JSON data
     *
     * @param {jQuery} widget - the widget
     * @param {object} data - the data as rendered by renderOptions
     * @param {bool} empty - no options available (don't bother retaining
     *                       the current value)
     */
    var updateOptions = function(widget, data, empty) {

        // Catch unsupported widget type
        if (widget.hasClass('checkboxes-widget-s3')) {
            s3_debug('filterOptionsS3 error: checkboxes-widget-s3 not supported, updateOptions aborted');
            return;
        }

        var options = data.options,
            newValue = data.defaultValue,
            hasCurrentValue = false;

        // Get the current value of the target field
        if (!empty) {
            var currentValue = '';
            if (widget.hasClass('checkboxes-widget-s3')) {
                // Checkboxes-widget-s3 target, not currently supported
                //currentValue = new Array();
                //widget.find('input:checked').each(function() {
                //   currentValue.push($(this).val());
                //});
                return;
            } else {
                // SELECT-based target (Select, MultiSelect, GroupedOpts)
                currentValue = widget.val();
                if (!currentValue) {
                    // Options list not populated yet?
                    currentValue = widget.prop('value');
                }
                if (currentValue && $(options).filter('option[value=' + currentValue + ']').length) {
                    hasCurrentValue = true;
                }
            }
            if (hasCurrentValue) {
                // Retain selected value
                newValue = currentValue;
            }
        }

        // Convert IS_ONE_OF_EMPTY <input> into a <select>
        // (Better use IS_ONE_OF_EMPTY_SELECT where possible)
        if (widget.prop('tagName') == 'INPUT') {
            var select = $('<select/>').addClass(widget.attr('class'))
                                       .attr('id', widget.attr('id'))
                                       .attr('name', widget.attr('name'))
                                       .data('visible', widget.data('visible'))
                                       .hide();
            widget.replaceWith(select);
            widget = select;
        }

        // Update the target field options
        widget.html(options)
              .val(newValue)
              .change()
              .prop('disabled', options === '');

        // Refresh groupedopts or multiselect
        if (widget.hasClass('groupedopts-widget')) {
            widget.groupedopts('refresh');
        } else if (widget.hasClass('multiselect-widget')) {
            widget.multiselect('refresh');
        }
        return widget;
    };

    /**
     * Replace the widget HTML with the data returned by Ajax request
     *
     * @param {jQuery} widget: the widget
     * @param {string} data: the HTML data
     */
    var replaceWidgetHTML = function(widget, data) {

        if (data !== '') {

            // Do we have a groupedopts or multiselect widget?
            var is_groupedopts = false,
                is_multiselect = false;
            if (widget.hasClass('groupedopts-widget')) {
                is_groupedopts = true;
            } else if (widget.hasClass('multiselect-widget')) {
                is_multiselect = true;
            }

            // Store selected value before replacing the widget HTML
            if (is_groupedopts || is_multiselect) {
                var widgetValue = null;
                if (widget.prop('tagName').toLowerCase() == 'select') {
                    widgetValue = widget.val();
                }
            }

            // Replace the widget with the HTML returned
            widget.html(data)
                  .change()
                  .prop('disabled', false);

            // Restore selected values if the options are still available
            if (is_groupedopts || is_multiselect) {
                if (widgetValue) {
                    var new_value = [];
                    for (var i=0, len=widgetValue.length, val; i<len; i++) {
                        val = widgetValue[i];
                        if (widget.find('option[value=' + val + ']').length) {
                            new_value.push(val);
                        }
                    }
                    widget.val(new_value).change();
                }
                // Refresh groupedopts/multiselect
                if (is_groupedopts) {
                    widget.groupedopts('refresh');
                } else {
                    widget.multiselect('refresh');
                }
            }
        } else {
            // Disable the widget
            widget.prop('disabled', true);
        }
        return widget;
    };

    /**
     * Update all targets in scope
     *
     * @param {jQuery} target - the target(s)
     * @param {string} lookupKey - the key to filter the records in the lookup table by,
     *                             usually the name of the field represented by the target
     * @param {string} value - the selected value in the trigger field (=the filter value)
     * @param {object} settings - the settings
     * @param {bool} userChange - this options update is triggered by a user action
     */
    var updateTarget = function(target, lookupKey, value, settings, userChange) {

        var multiple = false;
        if (target.length > 1) {
            if (target.first().attr('type') == 'checkbox') {
                var checkboxesWidget = target.first().closest('.checkboxes-widget-s3');
                if (checkboxesWidget) {
                    // Not currently supported => skip
                    s3_debug('filterOptionsS3 error: checkboxes-widget-s3 not supported, skipping');
                    return;
                    //target = checkboxesWidget;
                }
            } else {
                // Multiple rows inside an inline form
                multiple = true;
            }
        }

        if (multiple && settings.getWidgetHTML) {
            s3_debug('filterOptionsS3 warning: getWidgetHTML=true not suitable for multiple target widgets (e.g. inline rows)');
            target = target.first();
            multiple = false;
        }
        var requestTarget = multiple ? target.first() : target;

        // Abort previous request (if any)
        var previousRequest = requestTarget.data('update-request');
        if (previousRequest) {
            try {
                previousRequest.abort();
            } catch(err) {}
        }

        // Disable the target field if no value selected in trigger field
        if (value === '' || value === undefined) {
            target.prop('disabled', true);
            return;
        }

        // Construct the URL for the Ajax request
        var lookupResource = settings.lookupResource;
        var url;
        if (settings.lookupURL) {
            url = settings.lookupURL;
            if (value) {
                url = url.concat(value);
            }
        } else {
            var lookupPrefix = settings.lookupPrefix;
            url = S3.Ap.concat('/', lookupPrefix, '/', lookupResource, '.json');
            // Append lookup key to the URL
            var q;
            if (value) {
                q = lookupResource + '.' + lookupKey + '=' + value;
                if (url.indexOf('?') != -1) {
                    url = url.concat('&' + q);
                } else {
                    url = url.concat('?' + q);
                }
            }
        }
        var tooltip = settings.tooltip;
        if (tooltip) {
            tooltip = 'tooltip=' + tooltip;
            if (url.indexOf('?') != -1) {
                url = url.concat('&' + tooltip);
            } else {
                url = url.concat('?' + tooltip);
            }
        }

        var request = null;
        if (!settings.getWidgetHTML) {

            // Hide all visible targets and show throbber (remember visibility)
            target.each(function() {
                var widget = $(this),
                    visible = true;
                if (widget.hasClass('groupedopts-widget')) {
                    visible = widget.groupedopts('visible');
                } else {
                    visible = widget.is(':visible');
                }
                if (visible) {
                    widget.data('visible', true);
                    if (widget.hasClass('groupedopts-widget')) {
                        widget.groupedopts('hide');
                    } else {
                        widget.hide();
                    }
                    addThrobber(widget, lookupResource);
                } else {
                    widget.data('visible', false);
                }
            });

            // Send update request
            request = $.ajaxS3({
                url: url,
                dataType: 'json',
                success: function(data) {

                    // Render the options
                    var options = renderOptions(data, settings),
                        empty = data.length === 0 ? true : false;

                    // Apply to all targets
                    target.each(function() {

                        var widget = $(this);

                        // Update the widget
                        widget = updateOptions(widget, options, empty);

                        // Show the widget if it was visible before
                        if (widget.data('visible')) {
                            if (widget.hasClass('groupedopts-widget')) {
                                if (!empty) {
                                    widget.groupedopts('show');
                                }
                            } else {
                                widget.show();
                            }
                        }

                        // Remove throbber
                        removeThrobber(widget, lookupResource);
                    });

                    // Modify URL for Add-link and show the Add-link
                    updateAddResourceLink(lookupResource, lookupKey, value);

                    // Clear navigate-away-confirm if not a user change
                    if (!userChange) {
                        S3ClearNavigateAwayConfirm();
                    }
                }
            });

        } else {

            // Find the target widget
            var targetName = settings.targetWidget || target.attr('name');
            var widget = $('[name = "' + targetName + '"]'),
                visible = true,
                show_widget = false;

            // Hide the widget if it is visible, add throbber
            if (widget.hasClass('groupedopts-widget')) {
                visible = widget.groupedopts('visible');
            } else {
                visible = widget.is(':visible');
            }
            if (visible) {
                show_widget = true;
                widget.data('visible', true);
                if (widget.hasClass('groupedopts-widget')) {
                    widget.groupedopts('hide');
                } else {
                    widget.hide();
                }
                addThrobber(widget, lookupResource);
            }

            // Send update request
            request = $.ajaxS3({
                url: url,
                dataType: 'html',
                success: function(data) {

                    // Replace the widget HTML
                    widget = replaceWidgetHTML(widget, data, settings);

                    // Show the widget if it was visible before, remove throbber
                    if (show_widget) {
                        if (widget.hasClass('groupedopts-widget')) {
                            if (!empty) {
                                widget.groupedopts('show');
                            }
                        } else {
                            widget.show();
                        }
                    }
                    removeThrobber(widget, lookupResource);

                    // Modify URL for Add-link and show the Add-link
                    updateAddResourceLink(lookupResource, lookupKey, value);

                    // Clear navigate-away-confirm if not a user change
                    if (!userChange) {
                        S3ClearNavigateAwayConfirm();
                    }
                }
            });
        }
        requestTarget.data('update-request', request);
    };

    /**
     * Helper method to extract the trigger information, returns an
     * array with the actual trigger widget
     *
     * @param {jQuery} trigger - the trigger field(s)
     * @returns {array} [triggerField, triggerValue]
     */
    var getTriggerData = function(trigger) {

        var triggerField = trigger,
            triggerValue = '';
        if (triggerField.attr('type') == 'checkbox') {
            checkboxesWidget = triggerField.closest('.checkboxes-widget-s3');
            if (checkboxesWidget) {
                triggerField = checkboxesWidget;
            }
        }
        if (triggerField.length == 1 && !triggerField.hasClass('checkboxes-widget-s3')) {
            triggerValue = triggerField.val();
        } else if (triggerField.hasClass('checkboxes-widget-s3')) {
            triggerValue = new Array();
            triggerField.find('input:checked').each(function() {
                triggerValue.push($(this).val());
            });
        }
        return [triggerField, triggerValue];
    };

    /**
     * Main entry point, configures the event handlers
     *
     * @param {object} settings - the settings
     * @param {string|object} settings.trigger - the trigger (see getSelector)
     * @param {string|object} settings.target - the target (see getSelector)
     * @param {string} settings.scope - the event scope ('row' for current inline row,
     *                                  'form' for the master form)
     * @param {string} settings.event - the trigger event name
     *                                  (default: triggerUpdate.[trigger field name])
     * @param {string} settings.lookupKey - the field name to look up (default: trigger
     *                                      field name)
     * @param {string} settings.lookupField - the name of the field referenced by lookupKey,
     *                                        default: 'id'
     * @param {string} settings.lookupPrefix - the prefix (controller name) for the lookup
     *                                         URL, required
     * @param {string} settings.lookupResource - the resource name (function name) for the
     *                                           lookup URL, required
     * @param {string} settings.lookupURL - override lookup URL
     * @param {function} settings.fncPrep - preprocessing function for the JSON data (optional)
     * @param {function} settings.fncRepresent - representation function for the JSON data,
     *                                           optional, using record.name by default
     * @param {bool} settings.getWidgetHTML - lookup returns HTML (to replace the widget)
     *                                        rather than JSON data (to update it options)
     * @param {string} settings.targetWidget - alternative name-attribute for the target widget,
     *                                         overrides the selector generated from target-setting,
     *                                         not recommended
     * @param {bool} settings.showEmptyField - show an option for None if no options are
     *                                         available
     * @param {string} settings.msgNoRecords - show this text for the None-option
     * @param {bool} settings.optional - add a None-option (without text) even when options
     *                                   are available (so the user can select None)
     * @param {string} settings.tooltip - additional tooltip field to request from back-end,
     *                                    either a field selector or an expression "f(k,v)"
     *                                    where f is a function name that can be looked up
     *                                    from s3db, and k,v are field selectors for the row,
     *                                    f will be called with a list of tuples (k,v) for each
     *                                    row and is expected to return a dict {k:tooltip}
     */
    $.filterOptionsS3 = function(settings) {

        var trigger = settings.trigger, triggerName;


        if (settings.event) {
            triggerName = settings.event;
        } else if (typeof trigger == 'string') {
            triggerName = trigger;
        } else {
            triggerName = trigger.name;
        }

        var lookupKey = settings.lookupKey || triggerName,
            triggerSelector = getSelector(settings.trigger),
            targetSelector = getSelector(settings.target),
            triggerField,
            triggerForm,
            targetField,
            targetForm;

        if (!triggerSelector) {
            return;
        } else {
            triggerField = $(triggerSelector);
            if (!triggerField.length) {
                return;
            }
            triggerForm = triggerField.closest('form');
        }

        if (!targetSelector) {
            return;
        } else {
            targetField = $(targetSelector);
            if (!targetField.length) {
                return;
            }
            targetForm = targetField.closest('form');
        }

        // Initial event-less update of the target(s)
        $(triggerSelector).last().each(function() {
            var trigger = $(this),
                $scope;
            if (settings.scope == 'row') {
                $scope = trigger.closest('.edit-row.inline-form,.add-row.inline-form');
            } else {
                $scope = triggerForm;
            }
            var triggerData = getTriggerData(trigger),
                target = $scope.find(targetSelector);
            updateTarget(target, lookupKey, triggerData[1], settings, false);
        });

        // Change-event for the trigger fires trigger-event for the target
        // form, delegated to triggerForm so it happens also for dynamically
        // inserted triggers (e.g. inline forms)
        var changeEventName = 'change.s3options',
            triggerEventName = 'triggerUpdate.' + triggerName;
        triggerForm.undelegate(triggerSelector, changeEventName)
                   .delegate(triggerSelector, changeEventName, function() {
            var triggerData = getTriggerData($(this));
            targetForm.trigger(triggerEventName, triggerData);
        });

        // Trigger-event for the target form updates all targets within scope
        targetForm.on(triggerEventName, function(e, triggerField, triggerValue) {
            // Determine the scope
            var $scope;
            if (settings.scope == 'row') {
                $scope = triggerField.closest('.edit-row.inline-form,.add-row.inline-form');
            } else {
                $scope = triggerForm;
            }
            // Update all targets within scope
            var target = $scope.find(targetSelector);
            updateTarget(target, lookupKey, triggerValue, settings, true);
        });
    };
})(jQuery);

// ============================================================================
/**
 * Link any action buttons/link with the s3-cancel class to the referrer
 * (if on the same server and application), or to a default URL (if given),
 * or hide them if neither referrer nor default URL are available.
 */
(function() {

    /**
     * Strip query and hash from a URL
     *
     * @param {string} url - the URL
     */
    var stripQuery = function(url) {
        var newurl = url.split('?')[0].split('#')[0];
        return newurl;
    }

    /**
     * Main entry point
     *
     * @param {string} defaultURL - the default URL
     */
    $.cancelButtonS3 = function(defaultURL) {
        var cancelButtons = $('.s3-cancel');
        if (!cancelButtons.length) {
            return;
        }
        var referrer = document.referrer;
        if (referrer && stripQuery(referrer) != stripQuery(document.URL)) {
            var anchor = document.createElement('a');
            anchor.href = referrer;
            if (anchor.host == window.location.host &&
                anchor.pathname.lastIndexOf(S3.Ap, 0) === 0) {
                cancelButtons.attr('href', referrer);
            } else if (defaultURL) {
                cancelButtons.attr('href', defaultURL);
            } else {
                cancelButtons.hide();
            }
        } else if (defaultURL) {
            cancelButtons.attr('href', defaultURL);
        } else {
            cancelButtons.hide();
        }
    };
})(jQuery);

// ============================================================================
/**
 * Add a Slider to a field - used by S3SliderWidget
 */
S3.slider = function(fieldname, min, max, step, value) {
    var real_input = $('#' + fieldname);
    var selector = '#' + fieldname + '_slider';
    $(selector).slider({
        min: min,
        max: max,
        step: step,
        value: value,
        slide: function (event, ui) {
            // Set the value of the real input
            real_input.val(ui.value);
        },
        change: function(event, ui) {
            if (value == null) {
                // Set a default value
                // - halfway between min & max
                value = (min + max) / 2;
                // - rounded to nearest step
                var modulo = value % step;
                if (modulo != 0) {
                    if (modulo < (step / 2)) {
                        // round down
                        value = value - modulo;
                    } else {
                        // round up
                        value = value + modulo;
                    }
                }
                $(selector).slider('option', 'value', value);
                // Show the control
                $(selector + ' .ui-slider-handle').show();
                // Show the value
                // Hide the help text
                real_input.show().next().remove();
            }
        }
    });
    if (value == null) {
        // Don't show a value until Slider is touched
        $(selector + ' .ui-slider-handle').hide();
        // Show help text
        real_input.hide()
                  .after('<p>' + i18n.slider_help + '</p>');
    }
    // Enable the field before form is submitted
    real_input.closest('form').submit(function() {
        real_input.prop('disabled', false);
        // Normal Submit
        return true;
    });
};

/**
 * Add a Range Slider to a field - used by S3SliderFilter
 */
S3.range_slider = function(fieldname, min, max, step, values) {
    var real_input1 = $('#' + fieldname + '_1');
    var real_input2 = $('#' + fieldname + '_2');
    var selector = '#' + fieldname + '_slider';
    $(selector).slider({
        range: true,
        min: min,
        max: max,
        step: step,
        values: values,
        slide: function (event, ui) {
            // Set the value of the real inputs
            real_input1.val(ui.values[0]);
            real_input2.val(ui.values[1]);
        },
        change: function(event, ui) {
            if (value == null) {
                // Set a default value
                // - halfway between min & max
                value = (min + max) / 2;
                // - rounded to nearest step
                var modulo = value % step;
                if (modulo != 0) {
                    if (modulo < (step / 2)) {
                        // round down
                        value = value - modulo;
                    } else {
                        // round up
                        value = value + modulo;
                    }
                }
                $(selector).slider('option', 'values', values);
                // Show the control
                $(selector + ' .ui-slider-handle').show();
                // Show the value
                // Hide the help text
                real_input.show().next().remove();
            }
        }
    });
    if (values == []) {
        // Don't show a value until Slider is touched
        $(selector + ' .ui-slider-handle').hide();
        // Show help text
        real_input1.hide();
        real_input2.hide()
                   .after('<p>' + i18n.slider_help + '</p>');
    }
    // Enable the fields before form is submitted
    real_input1.closest('form').submit(function() {
        real_input1.prop('disabled', false);
        real_input2.prop('disabled', false);
        // Normal Submit
        return true;
    });
};

// ============================================================================
/**
 * Add a querystring variable to an existing URL and redirect into it.
 * It accounts for existing variables and will override an existing one.
 * Sample usage: _onchange="S3.reloadWithQueryStringVars({'_language': $(this).val()});")
 * used by IFRC layouts.py
 */

S3.reloadWithQueryStringVars = function(queryStringVars) {
    var existingQueryVars = location.search ? location.search.substring(1).split('&') : [],
        currentUrl = location.search ? location.href.replace(location.search, '') : location.href,
        newQueryVars = {},
        newUrl = currentUrl + '?';
    if (existingQueryVars.length > 0) {
        for (var i = 0; i < existingQueryVars.length; i++) {
            var pair = existingQueryVars[i].split('=');
            newQueryVars[pair[0]] = pair[1];
        }
    }
    if (queryStringVars) {
        for (var queryStringVar in queryStringVars) {
            newQueryVars[queryStringVar] = queryStringVars[queryStringVar];
        }
    }
    if (newQueryVars) {
        for (var newQueryVar in newQueryVars) {
            newUrl += newQueryVar + '=' + newQueryVars[newQueryVar] + '&';
        }
        newUrl = newUrl.substring(0, newUrl.length - 1);
        window.location.href = newUrl;
    } else {
        window.location.href = location.href;
    }
};

// ============================================================================
// Module pattern to hide internal vars
(function () {
    var deduplication = function() {
        // Deduplication event handlers
        $('.mark-deduplicate').click(function() {
            var url = $('#markDuplicateURL').attr('href');
            if (url) {
                $.ajaxS3({
                    type: 'POST',
                    url: url,
                    data: {},
                    dataType: 'JSON',
                    // gets moved to .done() inside .ajaxS3
                    success: function(data) {
                        $('.mark-deduplicate, .unmark-deduplicate, .deduplicate').toggleClass('hide');
                    }
                });
            }
        });
        $('.unmark-deduplicate').click(function() {
            var url = $('#markDuplicateURL').attr('href');
            if (url) {
                $.ajaxS3({
                    type: 'POST',
                    url: url + '?remove=1',
                    data: {},
                    dataType: 'JSON',
                    // gets moved to .done() inside .ajaxS3
                    success: function(data) {
                        $('.mark-deduplicate, .unmark-deduplicate, .deduplicate').toggleClass('hide');
                    }
                });
            }
        });
        $('.swap-button').click(function() {
            // Swap widgets between original and duplicate side
            var id = this.id;
            var name = id.slice(5);

            var original = $('#original_' + name);
            var original_id = original.attr('id');
            var original_name = original.attr('name');
            var original_parent = original.parent().closest('td.mwidget');
            var duplicate = $('#duplicate_' + name);
            var duplicate_id = duplicate.attr('id');
            var duplicate_name = duplicate.attr('name');
            var duplicate_parent = duplicate.parent().closest('td.mwidget');

            // Rename with placeholder names
            original.attr('id', 'swap_original_id');
            original.attr('name', 'swap_original_name');
            $('#dummy' + original_id).attr('id', 'dummy_swap_original_id');
            duplicate.attr('id', 'swap_duplicate_id');
            duplicate.attr('name', 'swap_duplicate_name');
            $('#dummy' + duplicate_id).attr('id', 'dummy_swap_duplicate_id');

            // Swap elements
            original_parent.before('<td id="swap_original_placeholder"></td>');
            var o = original_parent.detach();
            duplicate_parent.before('<td id="swap_duplicate_placeholder"></td>');
            var d = duplicate_parent.detach();
            $('#swap_original_placeholder').after(d);
            $('#swap_original_placeholder').remove();
            $('#swap_duplicate_placeholder').after(o);
            $('#swap_duplicate_placeholder').remove();

            // Rename to original names
            original.attr('id', duplicate_id);
            original.attr('name', duplicate_name);
            $('#dummy_swap_original_id').attr('id', 'dummy' + duplicate_id);
            duplicate.attr('id', original_id);
            duplicate.attr('name', original_name);
            $('#dummy_swap_duplicate').attr('id', 'dummy' + original_id);
        });
    };

    /**
     * Used by Themes with a Side-menu
     * - for long pages with small side menus, we want the side-menu to always be visible
     * BUT
     * - for short pages with large side-menus, we don't want the side-menu to scroll
     */
    var onResize = function() {
        // Default Theme
        var side_menu_holder = $('.aside');
        /* Doesn't work on IFRC
        if (!side_menu_holder.length) {
            // IFRC?
            side_menu_holder = $('#left-col');
        } */
        if (side_menu_holder.length) {
            // Default Theme
            var header = $('#menu_modules');
            if (!header.length) {
                // Bootstrap?
                header = $('#navbar-inner');
                if (!header.length) {
                    // IFRC?
                    header = $('#header');
                }
            }
            // Default Theme
            var side_menu = $('#menu_options');
            /* Doesn't work on IFRC
            if (!side_menu.length) {
                // IFRC?
                side_menu = $('#main-sub-menu');
            } */
            //var footer = $('#footer');
            //if ((header.height() + footer.height() + side_menu.height()) < $(window).height()) {
            if ((header.height() + side_menu.height() + 10) < $(window).height()) {
                side_menu_holder.css('position', 'fixed');
                $('#content').css('min-height', side_menu.height());
            } else {
                side_menu_holder.css('position', 'static');
            }
        }
    };

    // ========================================================================
    $(document).ready(function() {
        // Web2Py Layer
        $('.alert-error').hide().slideDown('slow');
        $('.alert-error').click(function() {
            $(this).fadeOut('slow');
            return false;
        });
        $('.alert-warning').hide().slideDown('slow');
        $('.alert-warning').click(function() {
            $(this).fadeOut('slow');
            return false;
        });
        $('.alert-info').hide().slideDown('slow');
        $('.alert-info').click(function() {
            $(this).fadeOut('slow');
            return false;
        });
        $('.alert-success').hide().slideDown('slow');
        $('.alert-success').click(function() {
            $(this).fadeOut('slow');
            return false;
        });
        $("input[type='checkbox'].delete").click(function() {
            if ((this.checked) && (!confirm(i18n.delete_confirmation))) {
                    this.checked = false;
            }
        });

        // If a form is submitted with errors, this will scroll
        // the window to the first form error message
        var inputErrorId = $('form .error[id]').eq(0).attr('id');
        if (inputErrorId != undefined) {
            inputName = inputErrorId.replace('__error', '');
            inputId = $('[name=' + inputName + ']').attr('id');
            inputLabel = $('[for=' + inputId + ']');
            try {
                window.scrollTo(0, inputLabel.offset().top);
            } catch(e) {}
        }

        // T2 Layer
        //try { $('.zoom').fancyZoom( {
        //    scaleImg: true,
        //    closeOnClick: true,
        //    directory: S3.Ap.concat('/static/media')
        //}); } catch(e) {}

        // S3 Layer
        // dataTables' delete button
        // (can't use S3.confirmClick as the buttons haven't yet rendered)
        if (S3.interactive) {
            $(document).on('click', 'a.delete-btn', function(event) {
                if (confirm(i18n.delete_confirmation)) {
                    return true;
                } else {
                    event.preventDefault();
                    return false;
                }
            });

            if (S3.FocusOnFirstField != false) {
                // Focus On First Field
                $('input:text:visible:first').focus();
            }
        }

        // Accept comma as thousands separator
        $('input.int_amount').keyup(function() {
            this.value = this.value.reverse()
                                   .replace(/[^0-9\-,]|\-(?=.)/g, '')
                                   .reverse();
        });
        $('input.float_amount').keyup(function() {
            this.value = this.value.reverse()
                                   .replace(/[^0-9\-\.,]|[\-](?=.)|[\.](?=[0-9]*[\.])/g, '')
                                   .reverse();
        });

        // Auto-capitalize first names
        $('input[name="first_name"]').focusout(function() {
            this.value = this.value.charAt(0).toLocaleUpperCase() + this.value.substring(1);
        });

        // ListCreate Views
        $('#show-add-btn').click(function() {
            // Hide the Button
            $('#show-add-btn').hide(10, function() {
                // Show the Form
                $('#list-add').slideDown('medium');
                // Resize any jQueryUI SelectMenu buttons
                $('.select-widget').selectmenu('refresh');
            });
        });

        // Resizable textareas
        $('textarea.resizable:not(.textarea-processed)').each(function() {
            var that = $(this);
            // Avoid non-processed teasers.
            if (that.is(('textarea.teaser:not(.teaser-processed)'))) {
                return false;
            }
            var textarea = that.addClass('textarea-processed');
            var staticOffset = null;
            // When wrapping the text area, work around an IE margin bug. See:
            // http://jaspan.com/ie-inherited-margin-bug-form-elements-and-haslayout
            that.wrap('<div class="resizable-textarea"><span></span></div>')
            .parent().append($('<div class="grippie"></div>').mousedown(startDrag));
            var grippie = $('div.grippie', that.parent())[0];
            grippie.style.marginRight = (grippie.offsetWidth - that[0].offsetWidth) + 'px';
            function startDrag(e) {
                staticOffset = textarea.height() - e.pageY;
                textarea.css('opacity', 0.25);
                $(document).mousemove(performDrag).mouseup(endDrag);
                return false;
            }
            function performDrag(e) {
                textarea.height(Math.max(32, staticOffset + e.pageY) + 'px');
                return false;
            }
            function endDrag(e) {
                $(document).unbind('mousemove', performDrag).unbind('mouseup', endDrag);
                textarea.css('opacity', 1);
            }
            return true;
        });

        // IE6 non anchor hover hack
        $('#modulenav .hoverable').hover(
            function() {
                $(this).addClass('hovered');
            },
            function() {
                $(this).removeClass('hovered');
            }
        );

        // Menu popups (works in IE6)
        $('#modulenav li').hover(
            function() {
                    var header_width = $(this).width();
                    var popup_width = $('ul', this).width();
                    if (popup_width !== null){
                      if (popup_width < header_width){
                        $('ul', this).css({
                            'width': header_width.toString() + 'px'
                        });
                      }
                    }
                    $('ul', this).css('display', 'block');
                },
            function() {
                $('ul', this).css('display', 'none');
            }
        );

        // Event Handlers for the page
        S3.redraw();

        // Popovers (Bootstrap themes only)
        if (typeof($.fn.popover) != 'undefined') {
            // Applies to elements created after $(document).ready
            $('body').popover({
                selector: '.s3-popover',
                trigger: 'hover',
                placement: 'left'
            });
        }

        // Handle Page Resizes
        onResize();
        $(window).bind('resize', onResize);

        // De-duplication Event Handlers
        deduplication();

        // UTC Offset
        now = new Date();
        $('form').append("<input type='hidden' value=" + now.getTimezoneOffset() + " name='_utc_offset'/>");

        // Social Media 'share' buttons
        if ($('#socialmedia_share').length > 0) {
            // DIV exists (deployment_setting on)
            var currenturl = document.location.href;
            var currenttitle = document.title;
            // Linked-In
            $('#socialmedia_share').append("<div class='socialmedia_element'><script src='//platform.linkedin.com/in.js'></script><script type='IN/Share' data-counter='right'></script></div>");
            // Twitter
            $('#socialmedia_share').append("<div class='socialmedia_element'><a href='https://twitter.com/share' class='twitter-share-button' data-count='none' data-hashtags='sahana-eden'>Tweet</a><script>!function(d,s,id){var js,fjs=d.getElementsByTagName(s)[0];if(!d.getElementById(id)){js=d.createElement(s);js.id=id;js.src='//platform.twitter.com/widgets.js';fjs.parentNode.insertBefore(js,fjs);}}(document,'script','twitter-wjs');</script></div>");
            // Facebook
            $('#socialmedia_share').append("<div class='socialmedia_element'><div id='fb-root'></div><script>(function(d, s, id) { var js, fjs = d.getElementsByTagName(s)[0]; if (d.getElementById(id)) return; js = d.createElement(s); js.id = id; js.src = '//connect.facebook.net/en_US/all.js#xfbml=1'; fjs.parentNode.insertBefore(js, fjs); }(document, 'script', 'facebook-jssdk'));</script> <div class='fb-like' data-send='false' data-layout='button_count' data-show-faces='true' data-href='" + currenturl + "'></div></div>");
        }

        // Form toggle (e.g. S3Profile update-form)
        $('.form-toggle').click(function() {
            var self = $(this),
                hidden = $(this).data('hidden');
            hidden = hidden && hidden != 'False';
            self.data('hidden', hidden ? false : true)
                .siblings().slideToggle('medium', function() {
                    self.children('span').each(function() {
                        $(this).text(hidden ? $(this).data('off') : $(this).data('on'))
                               .siblings().toggle();
                    });
                });
        });

        // Options Menu Toggle on mobile
        $('#menu-options-toggle').on('click', function(e) {
            e.stopPropagation();
            var $this = $(this);
            var status = $this.data('status'),
                menu = $('#menu-options');
            if (status == 'off') {
                menu.hide().removeClass('hide-for-small').slideDown(400, function() {
                    $this.data('status', 'on').text($this.data('on'));
                });
            } else {
                menu.slideUp(400, function() {
                    menu.addClass('hide-for-small').show();
                    $this.data('status', 'off').text($this.data('off'));
                });
            }
        });
    });

}());
// ============================================================================
