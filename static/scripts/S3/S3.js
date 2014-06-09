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
        var url_out = attr;
        if (caller) {
            caller = caller.replace(/__row_comment/, '') // DRRPP formstyle
                           .replace(/__row/, '');
            // Avoid Duplicate callers
            if (attr.indexOf('caller=') == -1) {
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
            // Lower the z-Index of the multiselect menu which opened us (if that's what we were opened from)
            //$('.ui-multiselect-menu').css('z-index', 1049);
            var caller = url.slice(i + 7);
            i = url.indexOf('&');
            if (i != -1) {
                caller = caller.slice(0, i - 1);
            }
            var select = $('#' + caller);
            if (select.hasClass('multiselect-widget')) {
                select.multiselect('close');
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
    })
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
}

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
}

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
 * Filter a select field based on a "filter field", eg:
 * - Competency Ratings filtered by Skill Type
 * - Item Packs filtered by Item
 * - Rooms filtered by Site
 * - Themes filtered by Sector
 **/

var S3OptionsFilter = function(settings) {
    /**
     * Settings:
     *          triggerName: the trigger field name (not the HTML element name)
     *          targetName: the target field name (not the HTML element name)
     *
     *          lookupPrefix: the lookup controller prefix
     *          lookupResource: the lookup resource (=function to call)
     *          lookupKey: the lookup key field name (default=triggerName)
     *          lookupField: the field to look up (default="id")
     *
     *          lookupURL: the lookup URL (optional)
     *          getWidgetHTML: the lookup URL returns the options widget as HTML
     *
     *          optional: target field value is optional (i.e. can be '', default=false)
     *          showEmptyField: show the empty options list (default=true)
     *          msgNoRecords: internationalized message for "no records"
     *          targetWidget: the target widget (if different from target field)
     *          fncPrep: function to pre-process the target options
     *          fncRepresent: function to represent the target options
     */

    var triggerName = settings.triggerName;
    var targetName = settings.targetName;

    // Selector for regular form fields: prefix_field
    var triggerSelector = '[name="' + triggerName + '"]';
    // Selector for inline-form fields: prefix_alias_field
    triggerSelector += ',[name*="_i_' + triggerName + '_edit_"]';

    // Find the trigger field
    var triggerField = $(triggerSelector);
    if (triggerField.length === 0) {
        // Trigger field not present
        return;
    }

    // Flag to show whether this is the first run
    var first = true;

    // Function to call when trigger field is changed
    var triggerFieldChange = function(event) {

        if (first) {
            var $triggerField = triggerField;
        } else {
            // Select the specific triggerField (inline form can contain multiple)
            var $triggerField = $(this);
        }
        var triggerFieldName = $triggerField.attr('name');

        // Find the target field
        if (triggerFieldName == triggerName) {
            // Regular form field
            var targetField = $('[name="' + targetName + '"]');
            if (targetField.length === 0) {
                return;
            }
            var targetSelector = targetField.attr('name');
        } else {
            // Inline field
            var names = triggerFieldName.split('_');
            var prefix = names[0];
            var rowindex = names.pop();
            var targetField = $('[name*="' + prefix + '_"][name*="_i_' + targetName + '_edit_' + rowindex + '"]');
            if (targetField.length === 0) {
                return;
            }
            var targetSelector = targetField.attr('name');
        }

        // Cancel previous Ajax request
        try {
            S3.JSONRequest[targetField.attr('id')].abort();
        } catch(err) {}

        // Get the lookup value from the trigger field
        var lookupValue = '';
        if ($triggerField.attr('type') == 'checkbox') {
            checkboxesWidget = $triggerField.closest('.checkboxes-widget-s3');
            if (checkboxesWidget) {
                $triggerField = checkboxesWidget;
            }
        }
        if ($triggerField.length == 1 && !$triggerField.hasClass('checkboxes-widget-s3')) {
            // SELECT
            lookupValue = $triggerField.val();
        } else if ($triggerField.length > 1) {
            // Checkboxes
            lookupValue = new Array();
            $triggerField.filter('input:checked').each(function() {
                lookupValue.push($(this).val());
            });
        } else if ($triggerField.hasClass('checkboxes-widget-s3')) {
            lookupValue = new Array();
            $triggerField.find('input:checked').each(function() {
                lookupValue.push($(this).val());
            });
        }

        // Disable the target field if no value selected
        if (lookupValue === '' || lookupValue === undefined) {
            targetField.prop('disabled', true);
            return;
        }

        // Get the current value of the target field
        var currentValue = '';
        if (targetField.length == 1) {
            // SELECT
            currentValue = targetField.val();
            if (!currentValue) {
                // Options list not populated yet?
                currentValue = targetField.attr('value'); // jQuery Migrate doesn't like this
            }
        } else if (targetField.length > 1) {
            // Checkboxes
            currentValue = new Array();
            targetField.filter('input:checked').each(function() {
                currentValue.push($(this).val());
            });
        }

        // Construct the URL for the Ajax request
        var lookupResource = settings.lookupResource;
        var url;
        if (settings.lookupURL) {
            url = settings.lookupURL;
            if (lookupValue) {
                url = url.concat(lookupValue);
            }
        } else {
            var lookupPrefix = settings.lookupPrefix;
            url = S3.Ap.concat('/', lookupPrefix, '/', lookupResource, '.json');
            // Append lookup key to the URL
            var q;
            if (lookupValue) {
                var lookupKey;
                if (typeof settings.lookupKey == 'undefined') {
                    // Same field name in both tables
                    lookupKey = settings.triggerName;
                } else {
                    lookupKey = settings.lookupKey;
                }
                q = lookupResource + '.' + lookupKey + '=' + lookupValue;
                if (url.indexOf('?') != -1) {
                    url = url.concat('&' + q);
                } else {
                    url = url.concat('?' + q);
                }
            }
            // Append the current value to the URL (what for?)
            if (currentValue) {
                q = 'value=' + currentValue;
                if (url.indexOf('?') != -1) {
                    url = url.concat('&' + q);
                } else {
                    url = url.concat('?' + q);
                }
            }
        }

        // Find the target widget and replace it by a throbber
        var targetWidget = settings.targetWidget || targetSelector;
        var widget = $('[name = "' + targetWidget + '"]');
        widget.hide();

        // Do we have a groupedopts or multiselect widget?
        var is_groupedopts = false,
            is_multiselect = false;
        if (widget.hasClass('groupedopts-widget')) {
            is_groupedopts = true;
            widget.groupedopts('hide');
        } else if (widget.hasClass('multiselect-widget')) {
            is_multiselect = true;
        }

        // Store selected values before Ajax-refresh
        var widget_value = null;
        if (widget.prop('tagName').toLowerCase() == 'select') {
            widget_value = widget.val();
        }

        // Show throbber while loading
        if ($('#' + lookupResource + '_throbber').length === 0 ) {
            widget.after('<div id="' + lookupResource + '_throbber" class="throbber"/>');
        }


        if (!settings.getWidgetHTML) {
            // URL returns the widget options as JSON
            S3.JSONRequest[targetField.attr('id')] = $.ajaxS3({
                url: url,
                dataType: 'json',
                // gets moved to .done() inside .ajaxS3
                success: function(data) {
                    // Read relevant options
                    if (settings.showEmptyField === 'undefined') {
                        var showEmptyField = true;
                    } else {
                        var showEmptyField = settings.showEmptyField;   
                    }
                    var fncPrep = settings.fncPrep || function(data) { return null; };
                    var fncRepresent = settings.fncRepresent || function(record) { return record.name; };
                    var lookupField = settings.lookupField || 'id';
                    var newValue;
                    var options = '';
                    var prepResult;

                    // Render options list
                    if (data.length === 0) {
                        // No options available
                        if (showEmptyField) {
                            newValue = 0;
                            var msgNoRecords = settings.msgNoRecords || '-';
                            options = '<option value="">' + msgNoRecords + '</options>';
                        }
                    } else {
                        // Render the options
                        // Pre-process the data
                        try {
                            prepResult = fncPrep(data);
                        } catch (e) {
                            prepResult = null;
                        }
                        options = '';
                        for (var i = 0; i < data.length; i++) {
                            if (i === 0) {
                                newValue = data[i][lookupField];
                            }
                            options += '<option value="' + data[i][lookupField] + '">';
                            options += fncRepresent(data[i], prepResult);
                            options += '</option>';
                        }
                        if (settings.optional) {
                            newValue = 0;
                            options = '<option value=""></option>' + options;
                        }
                        if (currentValue) {
                            newValue = currentValue;
                        }
                    }

                    // Convert IS_ONE_OF_EMPTY INPUT to a SELECT (better to do this server-side where-possible)
                    var html = targetField.parent().html();
                    if (html.slice(1, 6) == 'input') {
                        html = html.replace('<input', '<select');
                        targetField.parent().html(html);

                        // Re-apply event handlers (tooltips & modals)
                        S3.redraw();

                        // reselect since changed
                        targetField = $('[name = "' + targetSelector + '"]');
                    }
                    if (options !== '') {
                        targetField.html(options)
                                   // Set the current field value
                                   .val(newValue)
                                   .change()
                                   .prop('disabled', false)
                                   .show();
                    } else {
                        // No options available => disable the target field
                        targetField.prop('disabled', true)
                                   .show();
                    }

                    // Modify URL for Add-link and show the Add-link
                    var targetFieldAdd = $('#' + lookupResource + '_add');
                    if (targetFieldAdd.length !== 0) {
                        var href = targetFieldAdd.attr('href');
                        if (href.indexOf(triggerName) == -1) {
                            // Add to URL
                            href += '&' + triggerName + '=' + $triggerField.val();
                        } else {
                            // Update URL
                            var re = new RegExp(triggerName + '=.*', 'g');
                            href = href.replace(re, triggerName + '=' + $triggerField.val());
                        }
                        targetFieldAdd.attr('href', href)
                                      .show();
                    }

                    // Remove the throbber
                    $('#' + lookupResource + '_throbber').remove();
                    if (first) {
                        // Don't include this change in the deliberate changes
                        S3ClearNavigateAwayConfirm();
                        first = false;
                    }
                }
            });
        } else {
            // URL returns the widget as HTML
            S3.JSONRequest[targetField.attr('id')] = $.ajaxS3({
                url: url,
                dataType: 'html',
                // gets moved to .done() inside .ajaxS3
                success: function(data) {
                    if (data !== '') {
                        // Replace the target field with the HTML returned
                        widget.html(data)
                              .change()
                              .prop('disabled', false);

                        if (is_groupedopts || is_multiselect) {
                            // groupedopts or multiselect => refresh widget
                            if (widget_value) {
                                // Restore selected values if the options are still
                                // available
                                var new_value = [];
                                for (var i=0, len=widget_value.length, val; i<len; i++) {
                                    val = widget_value[i];
                                    if (widget.find('option[value=' + val + ']').length) {
                                        new_value.push(val);
                                    }
                                }
                                widget.val(new_value).change();
                            }
                            if (is_groupedopts) {
                                widget.groupedopts('refresh');
                            } else {
                                widget.multiselect('refresh');
                            }
                        } else {
                            widget.show();
                        }
                    } else {
                        // Disable the target field
                        widget.prop('disabled', true);
                    }
                    // Remove Throbber
                    $('#' + lookupResource + '_throbber').remove();
                    if (first) {
                        // Don't include this change in the deliberate changes
                        S3ClearNavigateAwayConfirm();
                        first = false;
                    }
                    // Restore event handlers (@todo: deprecate)
                    if (S3.inline_checkbox_events) {
                        S3.inline_checkbox_events();
                    }
                }
            });
        }
    };

    // Call function when trigger field changed
    triggerField.change(triggerFieldChange);

    // If the field value is empty - disable - but keep initial value
    triggerFieldChange();
};

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
            };
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

    });

}());
// ============================================================================
