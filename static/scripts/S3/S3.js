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
var S3 = {};
S3.gis = {};
S3.gis.options = {};
S3.timeline = {};
S3.JSONRequest = {}; // Used to store and abort JSON requests
//S3.TimeoutVar = {}; // Used to store and abort JSON requests

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
        var string = '',
            i = 0,
            c = 0,
            c1 = 0,
            c2 = 0;
        while ( i < utftext.length ) {
            c = utftext.charCodeAt(i);
            if (c < 128) {
                string += String.fromCharCode(c);
                i++;
            } else if ((c > 191) && (c < 224)) {
                c1 = utftext.charCodeAt(i+1);
                string += String.fromCharCode(((c & 31) << 6) | (c1 & 63));
                i += 2;
            } else {
                c1 = utftext.charCodeAt(i+1);
                c2 = utftext.charCodeAt(i+2);
                string += String.fromCharCode(((c & 15) << 12) | ((c1 & 63) << 6) | (c2 & 63));
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
    $('label[title][title!=""]').cluetip({splitTitle: '|', showTitle:false});
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
    $('.s3_add_resource_link, .s3_modal').off('.S3Modal')
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

        // Create an iframe
        var id = S3.uid(),
            dialog = $('<iframe>', {
                'id': id,
                // Start empty to prevent contents reload at
                // DOM re-insertion (=unnecessary HTTP request)
                'src': '',
                // Set initial 'loading' class to show spinner until contents loaded
                'class': 'loading',
                'load': function() {
                    // Call popup_loaded only once we have a src
                    if ($(this).attr('src')) {
                        S3.popup_loaded(id);
                    }
                },
                'marginWidth': '0',
                'marginHeight': '0',
                'frameBorder': '0'
            }).appendTo('body');

        // Create jQuery UI dialog
        var self = this;
        dialog.dialog({
            autoOpen: false,
            title: title,
            minHeight: 480,
            minWidth: 320,
            modal: true,
            closeText: '',
            open: function( /* event, ui */ ) {
                // Clicking outside of the popup closes it
                $('.ui-widget-overlay').bind('click', function() {
                    dialog.dialog('close');
                });
            },
            close: function( /* event, ui */ ) {
                if (self.parent) {
                    // There is a parent modal: refresh it to fix layout
                    var iframe = self.parent.$('iframe.ui-dialog-content');
                    var width = iframe.width();
                    iframe.width(0);
                    window.setTimeout(function() {
                        iframe.width(width);
                    }, 300);
                }
                // Clear src to prevent DOM manipulation from triggering
                // post-close contents reload (=unnecessary HTTP request)
                dialog.attr('src', '').remove();
            },
        });

        // Only now set the iframe source URL and open the dialog
        dialog.attr('src', url).dialog('open');

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

    // Adjust iframe width, then un-hide popup contents
    $('#' + id).removeClass('loading').width(width).contents().find('#popup').show();
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
// Auto-Totals
// - allow a field to default to the sum of a set of other fields, whilst still allowing manual entry
S3.autoTotals = function(sumField, sourceFields, tablename) {
    if (tablename === undefined) {
        // Assume that fieldnames include the tablename
        tablename = '';
    } else {
        // Prepend fieldnames with the tablename
        tablename = tablename + '_';
    }
    sumField = $('#' + tablename + sumField);
    var fieldname,
        value,
        total;
    for (var i = 0; i < sourceFields.length; i++) {
        fieldname = sourceFields[i];
        $('#' + tablename + fieldname).change(function() {
             total = 0;
             for (var j = 0; j < sourceFields.length; j++) {
                fieldname = sourceFields[j];
                value = $('#' + tablename + fieldname).val();
                if (value) {
                    total += parseInt(value);
                }
             }
             sumField.val(total)
                     .trigger('change'); // Cascade onwards
        });
    }
    // @ToDo?: Clear the sourceFields when the sumField is entered manually?
    // @ToDo?: Flag to show that the sumField has been set manually & so shouldn't be over-ridden by the source_fields
    //sumField.data('manual', true);
};

// ============================================================================
// Show Hiddens
// - allow a field to hide/unhide a set of other fields
S3.showHidden = function(controlField, affectedFields, tablename) {
    if (tablename === undefined) {
        // Assume that fieldnames include the tablename
        tablename = '';
    } else {
        // Prepend fieldnames with the tablename
        tablename = tablename + '_';
    }
    controlField = $('#' + tablename + controlField);
    controlField.change(function() {
        var fieldname,
            selector,
            i;
        if (controlField.prop('checked')) {
            // Show
            for (i = 0; i < affectedFields.length; i++) {
                fieldname = affectedFields[i];
                selector = '#' + tablename + fieldname;
                $(selector + '__row, ' + selector + '__subheading, ' + selector + '__subheading1, ' + selector + '__subheading2').show();
            }
        } else {
            // Hide
            for (i = 0; i < affectedFields.length; i++) {
                fieldname = affectedFields[i];
                selector = '#' + tablename + fieldname;
                $(selector + '__row, ' + selector + '__subheading, ' + selector + '__subheading1, ' + selector + '__subheading2').hide();
            }
        }
    });
    controlField.trigger('change');
};

// ============================================================================
S3.trunk8 = function(selector, lines, more) {
    // Line-truncation, see s3utils.s3_trunk8
    var settings = {
        fill: '&hellip; <a class="s3-truncate-more" href="#">' + more + '</a>'
        // Not yet working for me
        //parseHTML: true
    };
    if (lines) {
        settings.lines = lines;
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
    // Attach to any new items after Ajax-listUpdate (dataTables)
    $('.dataTable').on('draw.dt', function() {
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
                 .bind('keyup.maxLength', function() {
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
        var message = i18n.characters_left || 'characters left',
            input = $('#' + id),
            currentLength = input.val().length;
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
/**
 * Activate warning on exit without saving form data
 *
 * @param {Event} event - the event triggering the activation
 * @param {string} trigger - event parameter indicating the trigger
 *
 * Use element.trigger('change', 'implicit') instead of element.change()
 * to prevent activation if the event must be triggered for other reasons
 * than user input
 */
var S3SetNavigateAwayConfirm = function(event, trigger) {
    if (trigger !== 'implicit') {
        window.onbeforeunload = function() {
            return i18n.unsaved_changes;
        };
    }
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
        var form = $('form:not(.filter-form,.pt-form)');

        $('input, textarea', form).keypress(S3SetNavigateAwayConfirm)
                                  .change(S3SetNavigateAwayConfirm);
        $('select', form).change(S3SetNavigateAwayConfirm);
        form.submit(S3ClearNavigateAwayConfirm);
    });
};

// ============================================================================
(function($) {

    // Default AJAX settings
    $.ajaxS3Settings = {
        timeout : 10000, // 10s
        //msgTimeout: 2000,
        retryLimit: 5,
        dataType: 'json',
        async: true,
        type: 'GET'
    };

    /**
     * Wrapper for jQuery.ajax to handle poor network environments
     * - retries failed requests & alerts on errors
     *
     * @param {object} ajaxOptions - the Ajax options
     */
    function AjaxS3(ajaxOptions) {

        this.xhr = null;

        // Ajax options
        var options = $.extend({}, $.ajaxS3Settings, ajaxOptions);
        this.options = options;

        // Callbacks
        this.successCallback = ajaxOptions.success;
        this.errorCallback = ajaxOptions.error;

        // Prevent callbacks from being executed by $.ajax itself
        options.success = null;
        options.error = null;

        // Activity Message
        this.message = ajaxOptions.message;

        // Retry
        this.tryCount = 0;
        this.retryLimit = options.retryLimit;

        // Alerts
        this.alerts = [];
        this.ignoreStatus = options.ignoreStatus || [];
    }

    /**
     * Success callback
     *
     * @param {mixed} data - the data returned from server
     *
     * NB: executed in the context of the options object passed
     *     to $.ajax (=this), which holds the AjaxS3 instance as
     *     'AjaxS3' property
     */
    AjaxS3.prototype.onSuccess = function(data) {

        // Get the instance from context
        var self = this.AjaxS3;
        if (!self) {
            return;
        }

        // Reset try count and forget the xhr
        self.tryCount = 0;
        self.xhr = null;

        // Remove all warnings generated by this request
        S3.hideAlerts(self.alerts);

        // Show final success message
        if (data && data.message) {
            S3.showAlert(data.message, 'success');
        }

        // Apply the caller's success callback
        var successCallback = self.successCallback;
        if (successCallback) {
            successCallback.apply(this, arguments);
        }
    };

    /**
     * Error callback
     *
     * @param {jqXHR} jqXHR - the jqXHR object (extended XMLHttpRequest)
     * @param {string} textStatus - the final request status:
     *                              timeout|error|abort|parsererror
     *
     * NB: executed in the context of the options object passed
     *     to $.ajax (=this), which holds the AjaxS3 instance as
     *     'AjaxS3' property
     */
    AjaxS3.prototype.onFailure = function(jqXHR, textStatus) {

        // Get the instance form context
        var self = this.AjaxS3;
        if (!self) {
            return;
        }

        var httpStatus = jqXHR.status,
            readyState = jqXHR.readyState,
            navigateAway = !httpStatus && readyState === 0;

        if (textStatus == 'abort' || navigateAway) {

            // Request aborted, or navigating away...don't show nasty messages
            self.tryCount = 0;
            self.xhr = null;

            if (navigateAway) {
                return;
            }

        } else if (textStatus == 'timeout') {

            // Request timeout => retry?
            self.tryCount++;

            var tryCount = self.tryCount,
                message = self.message;

            if (tryCount <= self.retryLimit) {

                // Show retry-warning
                message = i18n.ajax_get + ' ' + (message ? message : i18n.ajax_fmd) + '... ' + i18n.ajax_rtr + ' ' + tryCount;
                self.alerts.push(S3.showAlert(message, 'warning'));

                // Send again
                self.send();
                return;

            } else {
                self.xhr = null;
            }

            // Show final error
            message = i18n.ajax_wht + ' ' + tryCount + ' ' + i18n.ajax_gvn;
            S3.showAlert(message, 'error');

        } else if (httpStatus == 500) {
            // Internal server error
            S3.showAlert(i18n.ajax_500, 'error');
        } else {
            // Other error or server unreachable
            if (self.ignoreStatus.indexOf(httpStatus) != -1) {
                // Status handled by caller => do not display alert
            } else {
                var responseJSON = jqXHR.responseJSON;
                if (responseJSON && responseJSON.message) {
                    // A json_message with a specific error text
                    S3.showAlert(responseJSON.message, 'error');
                } else {
                    // HTTP status code only
                    S3.showAlert(i18n.ajax_dwn, 'error');
                }
            }
        }

        // Apply the caller's error callback (except when navigating away)
        var errorCallback = self.errorCallback;
        if (errorCallback) {
            errorCallback.apply(this, arguments);
        }
    };

    /**
     * Start processing this instance
     * - shows initial activity message
     * - sends the request
     */
    AjaxS3.prototype.start = function() {

        if (this.xhr !== null) {
            // Already started
            return;
        }

        // Show initial message
        var message = this.message;
        if (message) {
            message = i18n.ajax_get + ' ' + (message ? message : i18n.ajax_fmd) + '...';
            this.alerts.push(S3.showAlert(message, 'info'));
        }

        // Send request
        this.send();

        return this;
    };

    /**
     * Send (or re-send) the request
     * - registers the deferred-handlers and passes the instance to
     *   their context object
     */
    AjaxS3.prototype.send = function() {

        var options = this.options;

        // Pass this instance to the deferred-handlers
        options.AjaxS3 = this;

        this.xhr = $.ajax(
            options
        ).done(function() {
            this.AjaxS3.onSuccess.apply(this, arguments);
        }).fail(function() {
            this.AjaxS3.onFailure.apply(this, arguments);
        });
    };

    /**
     * Abort the currently active jqXHR
     */
    AjaxS3.prototype.abort = function() {

        if (this.xhr) {
            this.xhr.abort();
            this.xhr = null;
        }
    };

    /**
     * Expose AjaxS3 in jQuery API ($.ajaxS3)
     */
    $.ajaxS3 = function(options) {

        return new AjaxS3(options).start();
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
        return $.ajaxS3({
            type: 'GET',
            url: url,
            async: !sync,
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
 * Display a message in the alerts section
 *
 * @param {string} message - the message to display
 * @param {string} type - the alert type:
 *                        'error', 'info', 'success', 'warning'
 * @param {function} callback - optional callback to run when the message is closed
 *
 * @returns {jQuery} - the DOM node of the new alert
 */
S3.showAlert = function(message, type, callback) {

    if (!type) {
        type = 'success';
    }
    var alertSpace = $('#alert-space'),
        alert = $('<div class="alert alert-' + type + '">' + message + '<button type="button" class="close" data-dismiss="alert">×</button></div>');

    alertSpace.append(alert).undelegate('.s3').delegate('.alert', 'click.s3', function() {
        $(this).fadeOut('slow').remove();
        if (callback) {
            callback();
        }
        return false;
    });
    return alert;
};

/**
 * Remove messages from the alerts section
 *
 * @param {string|Array} alerts - remove the specified alerts (optional):
 *                                => a string to specify an alert type
 *                                => an array of DOM nodes to specify specific alerts
 *                                => if omitted, all alerts in the alert-space will be
 *                                   removed
 */
S3.hideAlerts = function(alerts) {

    if (typeof alerts == 'string') {
        $('.alert-' + alerts).remove();
    } else if (alerts) {
        alerts.forEach(function(alert) {
            alert.remove();
        });
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
var s3_viewMap = function(location_id, iframe_height, popup, controller, func) {
    // Display a Feature on a BaseMap within an iframe
    var url = S3.Ap.concat('/gis/display_feature/') + location_id,
        $map = $('#map'),
        $iframe_map = $('#iframe-map'),
        curl = document.location.pathname.split("/");

    if (controller === undefined) {
        // Default to Master Record's Controller
        controller = curl[2];
    }
    if (func === undefined) {
        // Default to Master Record's Function
        func = curl[3];
    }
    url += '?c=' + controller + '&f=' + func;

    if ((curl.length > 6) && ($.isNumeric(curl[6]))) {
        // Component Record ID
        url += '&r=' + curl[6];
    } else if ((curl.length > 4) && ($.isNumeric(curl[4]))) {
        // Master Record ID
        url += '&r=' + curl[4];
    }

    if ($map.length == 0 || popup == 'True') {
        url += '&popup=1';
        S3.openPopup(url, true);
    } else {
        var toggleButton = function() {
            // Hide/Show the 'Close Map' button
            var closeMap = $('#close-iframe-map');
            if ($iframe_map.is(':visible')) {
                closeMap.css({
                    'display': ''
                });
            } else {
                closeMap.css({
                    'display': 'none'
                });
            }
        };
        var closeMap = function() {
            // Hide the Map
            $('#iframe-map').slideUp('medium');
            $('#close-iframe-map').css({
                'display': 'none'
            });
        };

        if ($iframe_map.length==0) {
            // 1st iframe to be loaded in 'map'
            var iframe = $("<iframe id='iframe-map' data-feature='" + location_id + "' style='border-style:none' width='100%' height='" + iframe_height + "' src='" + url + "' />"),
                closelink = $("<a class='button tiny' id='close-iframe-map'>" + i18n.close_map + "</a>");

            closelink.bind('click', closeMap);
            // Display Map
            $map.slideDown('medium');
            $map.append(iframe);
            $map.append($('<div style="margin-bottom:10px" />').append(closelink));
        } else {
            var fid = $iframe_map.attr('data-feature');
            if (fid == location_id) {
                // Same feature request. Display Map
                $iframe_map.slideToggle('medium', toggleButton);
            } else {
                $iframe_map.attr({
                    'src': url,
                    'data-feature': location_id
                });
                $iframe_map.slideDown('medium', toggleButton);
            }
        }
    }
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
    } else {
        S3.popupWin.focus();
    }
};

// ============================================================================
/**
 * Filter options of a drop-down field (=target) by the selection made
 * in another field (=trigger), e.g.:
 *   - Task Form: Activity options filtered by Project selection
 *
 * @todo: fix updateAddResourceLink
 * @todo: move into separate file and load only when needed?
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
     * @param {string} setting.inlineRows - the inline form has multiple rows, default: true
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
                rows = setting.inlineRows;
            if (rows === undefined) {
                rows = true;
            }
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
     * Update the AddResourceLink for the target with lookup key and
     * value, so that the popup can pre-populate them; or hide the
     * AddResourceLink if no trigger value has been selected
     *
     * @param {string} resourceName - the target resource name
     * @param {string} key - the lookup key
     * @param {string} value - the selected trigger value
     */
    var updateAddResourceLink = function(resourceName, key, value) {

        $('a#' + resourceName + '_add').each(function() {
            var search = this.search,
                queries = [],
                selectable = false;
            if (search) {
                var items = search.substring(1).split('&');
                items.forEach(function(item) {
                    if (decodeURIComponent(item.split('=')[0]) != key) {
                        queries.push(item);
                    }
                });
            }
            if (value !== undefined && value !== null) {
                var query = encodeURIComponent(key) + '=' + encodeURIComponent(value);
                queries.push(query);
                selectable = true;
            }
            if (queries.length) {
                search = '?' + queries.join('&');
            } else {
                search = '';
            }
            var href = this.protocol + '//' + this.host + this.pathname + search + this.hash,
                $this = $(this).attr('href', href);
            if (selectable) {
                $this.parent().show();
            } else {
                $this.parent().hide();
            }
        });
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
                name,
                title;

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
                    title = '';
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
            selectedValues = [];

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
                if (!$.isArray(currentValue)) {
                    currentValue = [currentValue];
                }
                for (var i = 0, len = currentValue.length, val; i < len; i++) {
                    val = currentValue[i];
                    if (val && $(options).filter('option[value=' + val + ']').length) {
                        selectedValues.push(val);
                    }
                }
            }
            if (selectedValues.length) {
                // Retain selected value
                newValue = selectedValues;
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
        var disable = options === '';
        widget.html(options)
              .val(newValue)
              .change()
              .prop('disabled', disable);

        // Refresh groupedopts or multiselect
        if (widget.hasClass('groupedopts-widget')) {
            widget.groupedopts('refresh');
        } else if (widget.hasClass('multiselect-widget')) {
            widget.multiselect('refresh');
            // Disabled-attribute not reflected by refresh (?)
            if (!disable) {
                widget.multiselect('enable');
            } else {
                widget.multiselect('disable');
            }
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
            var widgetValue;
            if (is_groupedopts || is_multiselect) {
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
        var lookupResource = settings.lookupResource;
        if (value === '' || value === null || value === undefined) {
            target.val('').prop('disabled', true);
            if (target.multiselect('instance')) {
                target.multiselect('refresh')
                      .multiselect('disable');
            }
            // Trigger change-event on target for filter cascades
            target.change();
            updateAddResourceLink(lookupResource, lookupKey);
            return;
        }

        // Construct the URL for the Ajax request
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

        // Represent options unless settings.represent is falsy
        var represent = settings.represent;
        if (represent || typeof represent == 'undefined') {
            if (url.indexOf('?') != -1) {
                url = url.concat('&represent=1');
            } else {
                url = url.concat('?represent=1');
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
                    visible = widget.data('visible') || widget.is(':visible');
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
                visible = widget.data('visible') || widget.is(':visible');
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
                            if (widget.find('option').length) {
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
            var checkboxesWidget = triggerField.closest('.checkboxes-widget-s3');
            if (checkboxesWidget) {
                triggerField = checkboxesWidget;
            }
        }
        if (triggerField.hasClass('checkboxes-widget-s3')) {
            triggerValue = [];
            triggerField.find('input:checked').each(function() {
                triggerValue.push($(this).val());
            });
        } else if (triggerField.hasClass('s3-hierarchy-input')) {
            triggerValue = '';
            var value = triggerField.val();
            if (value) {
                value = JSON.parse(value);
                if (value.constructor === Array) {
                    if (value.length) {
                        triggerValue = value[0];
                    }
                } else
                if (!!value) {
                    triggerValue = value;
                }
            }
        } else if (triggerField.length == 1) {
            triggerValue = triggerField.val();
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
            targetField,
            targetForm;

        if (!targetSelector) {
            return;
        } else {
            targetField = $(targetSelector);
            if (!targetField.length) {
                return;
            }
            targetForm = targetField.closest('form');
        }

        if (!triggerSelector) {
            return;
        } else {
            // Trigger must be in the same form as target
            triggerField = targetForm.find(triggerSelector);
            if (!triggerField.length) {
                return;
            }
        }

        // Initial event-less update of the target(s)
        $(triggerSelector).each(function() {
            var trigger = $(this),
                $scope;
            // Hidden inline rows must not trigger an initial update
            // @note: check visibility of the row not of the trigger, e.g.
            //        AutoComplete triggers are always hidden!
            // @note: must check for CSS explicitly, not just visibility because
            //        the entire form could be hidden (e.g. list-add)
            var inlineRow = trigger.closest('.inline-form');
            if (inlineRow.length && (inlineRow.hasClass('empty-row') || inlineRow.css('display') == 'none')) {
                return;
            }
            if (settings.scope == 'row') {
                $scope = trigger.closest('.edit-row.inline-form,.add-row.inline-form');
            } else {
                $scope = targetForm;
            }
            var triggerData = getTriggerData(trigger),
                target = $scope.find(targetSelector);
            updateTarget(target, lookupKey, triggerData[1], settings, false);
        });

        // Change-event for the trigger fires trigger-event for the target
        // form, delegated to targetForm so it happens also for dynamically
        // inserted triggers (e.g. inline forms)
        var changeEventName = 'change.s3options',
            triggerEventName = 'triggerUpdate.' + triggerName;
        targetForm.undelegate(triggerSelector, changeEventName)
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
                $scope = targetForm;
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
    };

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
        change: function( /* event, ui */ ) {
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
            var value = ui.value,
                index = ui.handleIndex,
                real_input = $('#' + fieldname + '_' + (index + 1));
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
                $(selector).slider('option', 'values', index, value);
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
                    success: function( /* data */ ) {
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
                    success: function( /* data */ ) {
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

        // T2 Layer
        //try { $('.zoom').fancyZoom( {
        //    scaleImg: true,
        //    closeOnClick: true,
        //    directory: S3.Ap.concat('/static/media')
        //}); } catch(e) {}

        // S3 Layer

        // If a form is submitted with errors, this will scroll
        // the window to the first form error message
        var inputErrorId = $('form .error[id]').eq(0).attr('id');
        if (inputErrorId != undefined) {
            var inputName = inputErrorId.replace('__error', ''),
                inputId = $('[name=' + inputName + ']').attr('id'),
                inputLabel = $('[for=' + inputId + ']');
            try {
                window.scrollTo(0, inputLabel.offset().top);
                // Prevent first-field focus from scrolling back to
                // the top of the form again:
                S3.FocusOnFirstField = false;
            } catch(e) {}
        }

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

        // Ensure that phone fields appear with + at beginning not end in RTL
        if (S3.rtl) {
            $('.phone-widget').each(function() {
                // When form initially renders, ensure the LTR mark is placed at the beginning so that it looks correct
                // http://www.fileformat.info/info/unicode/char/200e/index.htm
                var value = this.value;
                if (value && (value.charAt(0) != '\u200E')) {
                    this.value = '\u200E' + value;
                }
            });
            $('.phone-widget').focusout(function() {
                var value = this.value;
                if (value) {
                    // When new data is entered then:
                    // 1. Ensure the LTR mark is placed at the beginning so that it looks correct
                    // 2. Ensure that if there is a trailing + then it is moved to the beginning
                    if (value.charAt(0) != '\u200E') {
                        if (value.charAt(value.length - 1) == '+') {
                            this.value = '\u200E' + '+' + value.substr(0, value.length - 2);
                        } else {
                            this.value = '\u200E' + value;
                        }
                    } else {
                         if (value.charAt(value.length - 1) == '+') {
                            this.value = '\u200E' + '+' + value.substr(1, value.length - 2);
                        }
                    }
                }
            });
        }

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
            function endDrag( /* e */ ) {
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

        // Timezone and UTC Offset
        var anyform = $('form');
        if (anyform.length) {
            var now = new Date(),
                tz;
            anyform.append("<input type='hidden' value='" + now.getTimezoneOffset() + "' name='_utc_offset'/>");
            try {
                tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
            } catch(e) {
                // not supported
            }
            if (tz) {
                anyform.append("<input type='hidden' value='" + tz + "' name='_timezone'/>");
            }
        }

        // Social Media 'share' buttons
        if ($('#socialmedia_share').length > 0) {
            // DIV exists (deployment_setting on)
            var currenturl = document.location.href;
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
        $('#menu-options-toggle,#list-filter-toggle').on('click', function(e) {
            e.stopPropagation();
            var $this = $(this);
            var status = $this.data('status'),
                menu;
            if (this.id == 'menu-options-toggle') {
                menu = $('#menu-options');
            } else {
                menu = $('#list-filter');
            }
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

        /**
         * Click-handler for s3-download-buttons:
         *
         * - any action item with a class 's3-download-button' and
         *   a 'url' data property (data-url)
         *
         * - for download of server-generated attachments, e.g. XLS or PDF
         *
         * - downloads the target document in a hidden iframe, which, if
         *   the file is sent with content-disposition "attachment", will
         *   only open the file dialog and nothing else
         *
         * - if this fails, the response will be opened in a modal dialog
         *   (JSON messages will be handled with a simple alert-box, though)
         */
        $('.s3-download-button').on('click', function(e) {

            // Do nothing else
            e.preventDefault();
            e.stopPropagation();

            var url = $(this).data('url');
            if (!url) {
                return;
            }

            // Re-use it if it already exists
            var iframe = document.getElementById("s3-download");
            if (iframe == null) {
               iframe = document.createElement('iframe');
               iframe.id = "s3-download";
               iframe.style.visibility = 'hidden';
               document.body.appendChild(iframe);
            }

            $('#s3-download').off('load').on('load', function() {
                // This event is only fired when contents was loaded into the
                // hidden iframe rather than downloaded as attachment, which
                // should only happen if there was some kind of error
                var message,
                    self = $(this);
                try {
                    // Try to parse the JSON message
                    message = JSON.parse(this.contentDocument.body.textContent).message;
                } catch(e) {
                    // No JSON message => show iframe contents as-is in a modal
                    self.dialog({
                        title: 'Download failed',
                        width: 500,
                        height: 300,
                        close: function() {
                            self.attr('src', '').remove();
                        }
                    }).css({
                        visibility: 'visible',
                        width: '100%'
                    });
                    return;
                }
                alert(message);
            });

            iframe.src = url;
            return false;
        });
    });

}());
// ============================================================================
