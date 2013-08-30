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
S3.TimeoutVar = Object(); // Used to store and abort JSON requests

S3.uid = function() {
    // Generate a random uid
    // Used for Popups on Map & jQueryUI modals
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
    $('.s3_add_resource_link, .s3_modal').unbind('click')
                                         .click(function() {
        var title = this.title;
        var url = this.href;
        var id = S3.uid();
        // Open a jQueryUI Dialog showing a spinner until iframe is loaded
        var dialog = $('<iframe id="' + id + '" class="loading" src=' + url + ' marginWidth="0" marginHeight="0" frameBorder="0" scrolling="auto" onload="S3.popup_loaded(\'' + id + '\')" style = "width:740px;"></iframe>')
                      .appendTo('body');
        dialog.dialog({
            // add a close listener to prevent adding multiple divs to the document
            close: function(event, ui) {
                // remove div with all data and events
                dialog.remove();
            },
            minHeight: 500,
            modal: true,
            open: function(event, ui) {
                $('.ui-widget-overlay').bind('click', function() {
                    dialog.dialog('close');
                });
            },
            title: title,
            width: 750,
            closeText: ''
        });
        // Prevent browser from following link
        return false;
    })
};
S3.popup_loaded = function(id) {
    // Resize the iframe to fit the Dialog
    var width = $('.ui-dialog').width() - 10;
    $('#' + id).css({width: width})
               // Display the hidden form
               .contents().find('#popup form').show();
}
function s3_popup_remove() {
    // Close jQueryUI Dialog Modal Popup
    $('iframe.ui-dialog-content').dialog('close');
}

$(document).ready(function() {
    // Web2Py Layer
    $('.error').hide().slideDown('slow');
    $('.error').click(function() {
        $(this).fadeOut('slow');
        return false;
    });
    $('.warning').hide().slideDown('slow');
    $('.warning').click(function() {
        $(this).fadeOut('slow');
        return false;
    });
    $('.information').hide().slideDown('slow');
    $('.information').click(function() {
        $(this).fadeOut('slow');
        return false;
    });
    $('.confirmation').hide().slideDown('slow');
    $('.confirmation').click(function() {
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
        window.scrollTo(0, inputLabel.offset().top);
    }

    // T2 Layer
    //try { $('.zoom').fancyZoom( {
    //    scaleImg: true,
    //    closeOnClick: true,
    //    directory: S3.Ap.concat('/static/media')
    //}); } catch(e) {}

    // S3 Layer
    // dataTables' delete button
    // (can't use S3ConfirmClick as the buttons haven't yet rendered)
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

    // jQueryUI Dialog Modal Popups
    S3.addModals();

    // Help Tooltips
    S3.addTooltips();

    // De-duplication Event Handlers
    S3.deduplication();

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

function s3_get_client_location(targetfield) {
   // Geolocation
   if (navigator.geolocation) {
    	navigator.geolocation.getCurrentPosition(function(position) {
			var clientlocation = position.coords.latitude + '|' + position.coords.longitude + '|' + position.coords.accuracy;
			targetfield.val(clientlocation);
    	});
    }
}

// ============================================================================
S3.deduplication = function() {
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

// ============================================================================
function S3ConfirmClick(ElementID, Message) {
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
}

// ============================================================================
// Code to warn on exit without saving
function S3SetNavigateAwayConfirm() {
    window.onbeforeunload = function() {
        return i18n.unsaved_changes;
    };
}

function S3ClearNavigateAwayConfirm() {
    window.onbeforeunload = function() {};
}

function S3EnableNavigateAwayConfirm() {
    $(document).ready(function() {
        if ( $('[class=error]').length > 0 ) {
            // If there are errors, ensure the unsaved form is still protected
            S3SetNavigateAwayConfirm();
        }
        var form = 'form:not(form.filter-form)',
            input = 'input:not(input[id=gis_location_advanced_checkbox])',
            select = 'select';
        $(form + ' ' + input).keypress( S3SetNavigateAwayConfirm );
        $(form + ' ' + input).change( S3SetNavigateAwayConfirm );
        $(form + ' ' + select).change( S3SetNavigateAwayConfirm );
        $('form').submit( S3ClearNavigateAwayConfirm );
    });
}

// ============================================================================
/**
 * ajaxS3
 * added by sunneach 2010-feb-14
 */

(function($) {
    // Default AJAX settings
    $.ajaxS3Settings = {
        timeout : 10000,
        msgTimeout: 2000,
        retryLimit : 10,
        dataType: 'json',
        async: true,
        type: 'GET'
    };

    // Wrapper for jQuery's .ajax to provide notifications on errors
    $.ajaxS3 = function(s) {
        var options = $.extend( {}, $.ajaxS3Settings, s );
        options.tryCount = 0;
        options.error = null;   // prevent callback from being executed twice
        options.success = null; // prevent callback from being executed twice
        if (s.message) {
            s3_showStatus(i18n.ajax_get + ' ' + (s.message ? s.message : i18n.ajax_fmd) + '...', this.ajaxS3Settings.msgTimeout);
        }
        $.ajax(
            options
        ).done(function(data, status) {
            s3_hideStatus();
            if (s.success) {
                s.success(data, status);
            }
        }).fail(function(jqXHR, textStatus, errorThrown) {
            if (textStatus == 'timeout') {
                this.tryCount++;
                if (this.tryCount <= this.retryLimit) {
                    // try again
                    s3_showStatus(i18n.ajax_get + ' ' + (s.message ? s.message : i18n.ajax_fmd) + '... ' + i18n.ajax_rtr + ' ' + this.tryCount,
                        $.ajaxS3Settings.msgTimeout);
                    $.ajax(this);
                    return;
                }
                s3_showStatus(i18n.ajax_wht + ' ' + (this.retryLimit + 1) + ' ' + i18n.ajax_gvn,
                    $.ajaxS3Settings.msgTimeout, false, true);
                if (s.error) {
                    s.error(jqXHR, textStatus, errorThrown);
                }
                return;
            }
            if (jqXHR.status == 500) {
                s3_showStatus(i18n.ajax_500, $.ajaxS3Settings.msgTimeout, false, true);
            } else {
                s3_showStatus(i18n.ajax_dwn, $.ajaxS3Settings.msgTimeout, false, true);
            }
            if (s.error) {
                s.error(jqXHR, textStatus, errorThrown);
            }
        });
    };

    // Simplified wrappers for .ajaxS3
    $.getS3 = function(url, data, callback, type, message, sync) {
        // shift arguments if data argument was omitted
        if ( $.isFunction( data ) ) {
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
        if ( $.isFunction( data ) ) {
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
 * status bar for ajaxS3 operation
 * taken from http://www.west-wind.com/WebLog/posts/388213.aspx
 * added and fixed by sunneach on Feb 16, 2010
 *
 *  to use make a call:
 *  s3_showStatus(message, timeout, additive, isError)
 *     1. message  - string - message to display
 *     2. timeout  - integer - milliseconds to change the statusbar style - flash effect (1000 works OK)
 *     3. additive - boolean - default false - to accumulate messages in the bar
 *     4. isError  - boolean - default false - show in the statusbarerror class
 *
 *  to remove bar, use
 *  s3_hideStatus()
 */
function S3StatusBar(sel, options) {
    var _I = this;
    var _sb = null;
    // options
    // ToDo allow options passed-in to over-ride defaults
    this.elementId = '_showstatus';
    this.prependMultiline = true;
    this.showCloseButton = false;
    this.afterTimeoutText = null;

    this.cssClass = 'statusbar';
    this.highlightClass = 'statusbarhighlight';
    this.errorClass = 'statusbarerror';
    this.closeButtonClass = 'statusbarclose';
    this.additive = false;
    $.extend(this, options);
    if (sel) {
      _sb = $(sel);
    }
    // Create statusbar object manually
    if (!_sb) {
        _sb = $("<div id='_statusbar' class='" + _I.cssClass + "'>" +
                "<div class='" + _I.closeButtonClass +  "'>" +
                (_I.showCloseButton ? ' X </div></div>' : '') )
                .appendTo(document.body)
                .show();
    }
    //if (_I.showCloseButton)
        $('.' + _I.cssClass).click(function(e) { $(_sb).hide(); });
    this.show = function(message, timeout, additive, isError) {
        if (additive || ((additive == undefined) && _I.additive)) {
            var html = "<div style='margin-bottom: 2px;' >" + message + '</div>';
            if (_I.prependMultiline) {
                _sb.prepend(html);
            } else {
                _sb.append(html);
            }
        } else {
            if (!_I.showCloseButton) {
                _sb.text(message);
            } else {
                var t = _sb.find('div.statusbarclose');
                _sb.text(message).prepend(t);
            }
        }
        _sb.show();
        if (timeout) {
            if (isError) {
                _sb.addClass(_I.errorClass);
            } else {
                _sb.addClass(_I.highlightClass);
            }
            setTimeout(
                function() {
                    _sb.removeClass(_I.highlightClass);
                    if (_I.afterTimeoutText) {
                       _I.show(_I.afterTimeoutText);
                    }
                },
                timeout);
        }
    };
    this.release = function() {
        if (_statusbar) {
            $('#_statusbar').remove();
            _statusbar = undefined;
        }
    };
}
// Use this as a global instance to customize constructor
// or do nothing and get a default status bar
var _statusbar = null;
function s3_showStatus(message, timeout, additive, isError) {
    if (!_statusbar) {
        _statusbar = new S3StatusBar();
    }
    _statusbar.show(message, timeout, additive, isError);
}
function s3_hideStatus() {
    if (_statusbar) {
        _statusbar.release();
    }
}

// ============================================================================
function s3_viewMap(feature_id) {
    // Display a Feature on a BaseMap within an iframe
    var url = S3.Ap.concat('/gis/display_feature/') + feature_id;
    var oldhtml = $('#map').html();
    var iframe = "<iframe width='640' height='480' src='" + url + "'></iframe>";
    var closelink = $('<a href=\"#\">' + i18n.close_map + '</a>');

    // @ToDo: Also make the represent link act as a close
    closelink.bind( "click", function(evt) {
        $('#map').html(oldhtml);
        evt.preventDefault();
    });

    $('#map').html(iframe);
    $('#map').append($("<div style='margin-bottom: 10px' />").append(closelink));
}
function s3_viewMapMulti(module, resource, instance, jresource) {
    // Display a set of Features on a BaseMap within an iframe
    var url = S3.Ap.concat('/gis/display_feature//?module=') + module + '&resource=' + resource + '&instance=' + instance + '&jresource=' + jresource;
    var oldhtml = $('#map').html();
    var iframe = '<iframe width="640" height="480" src="' + url + '"></iframe>';
    var closelink = $('<a href=\"#\">' + i18n.close_map + '</a>');

    // @ToDo: Also make the represent link act as a close
    closelink.bind( 'click', function(evt) {
        $('#map').html(oldhtml);
        evt.preventDefault();
    });

    $('#map').html(iframe);
    $('#map').append($("<div style='margin-bottom: 10px' />").append(closelink));
}
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
}
function s3_showMap(feature_id) {
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
}

// ============================================================================
/**
 * Re-usable function to filter a select field based on a "filter field", eg:
 * Competency Ratings filtered by Skill Type
 * Item Packs filtered by Item
 * Rooms filtered by Site
 * Themes filtered by Sector
 **/

function S3OptionsFilter(settings) {
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

    triggerField.change(function() {
        var triggerField = $(this);
        var triggerSelector = triggerField.attr('name');

        // Find the target field
        var targetSelector, targetField;
        if (triggerSelector == triggerName) {
            // Regular form field
            targetField = $('[name="' + targetName + '"]');
            if (targetField.length === 0) {
                return;
            }
            targetSelector = targetField.attr('name');
        } else {
            // Inline field
            var names = triggerSelector.split('_');
            var prefix = names[0];
            var rowindex = names.pop();
            targetField = $('[name*="' + prefix + '_"][name*="_i_' + targetName + '_edit_' + rowindex + '"]');
            if (targetField.length === 0) {
                return;
            }
            targetSelector = targetField.attr('name');
        }

        // Cancel previous Ajax request
        try {
            S3.JSONRequest[targetField.attr('id')].abort();
        } catch(err) {}

        // Get the lookup value from the trigger field
        var lookupValue = '';
        if (triggerField.attr('type') == 'checkbox') {
            checkboxesWidget = triggerField.closest('.checkboxes-widget-s3');
            if (checkboxesWidget) {
                triggerField = checkboxesWidget;
            }
        }
        if (triggerField.length == 1 && !triggerField.hasClass('checkboxes-widget-s3')) {
            // SELECT
            lookupValue = triggerField.val();
        } else if (triggerField.length > 1) {
            // Checkboxes
            lookupValue = new Array();
            triggerField.filter('input:checked').each(function() {
                lookupValue.push($(this).val());
            });
        } else if (triggerField.hasClass('checkboxes-widget-s3')) {
            lookupValue = new Array();
            triggerField.find('input:checked').each(function() {
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
                currentValue = targetField.attr('value');
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

        // Construct the Ajax context
        var context = {
            triggerSelector: triggerSelector,
            targetSelector: targetSelector,
            currentValue: currentValue,
            lookupResource: lookupResource,
            triggerName: triggerName
        };
        // Field to look up
        if (settings.lookupField) {
            context['lookupField'] = settings.lookupField;
        } else {
            context['lookupField'] = 'id';
        }
        // Show an empty select?
        if (settings.optional) {
            context['optional'] = settings.optional;
        } else {
            context['optional'] = false;
        }
        if (settings.showEmptyField) {
            context['showEmptyField'] = settings.showEmptyField;
        } else {
            context['showEmptyField'] = true;
        }
        // Message for no records
        if (settings.msgNoRecords) {
            context['msgNoRecords'] = settings.msgNoRecords;
        } else {
            context['msgNoRecords'] = '-';
        }
        // Representation of the target options
        if (settings.fncPrep) {
            context['fncPrep'] = settings.fncPrep;
        } else {
            context['fncPrep'] = function(data) { return null; };
        }
        if (settings.fncRepresent) {
            context['fncRepresent'] = settings.fncRepresent;
        } else {
            context['fncRepresent'] = function(record) { return record.name; };
        }

        // Find the target widget and replace it by a throbber
        var targetWidget;
        if (settings.targetWidget != undefined) {
            targetWidget = settings.targetWidget;
        } else {
            targetWidget = targetSelector;
        }
        context['targetWidget'] = targetWidget;
        var widget = $('[name = "' + targetWidget + '"]');
        widget.hide();
        if ($('#' + lookupResource + '_ajax_throbber').length === 0 ) {
            widget.after('<div id="' + lookupResource + '_ajax_throbber" class="ajax_throbber"/>');
        }

        if (!settings.getWidgetHTML) {
            // URL returns the widget options as JSON
            S3.JSONRequest[targetField.attr('id')] = $.ajax({
                url: url,
                dataType: 'json',
                context: context
            }).done(function(data) {
                // Pre-process the data
                var fncPrep = this.fncPrep;
                var prepResult;
                try {
                    prepResult = fncPrep(data);
                } catch (e) {
                    prepResult = null;
                }

                // Render options list
                var fncRepresent = this.fncRepresent;
                var FilterField = this.FilterField;
                var FieldResource = this.FieldResource;
                var triggerField = $('[name = "' + FilterField + '"]');
                var options = '';
                var currentValue;
                if (data.length === 0) {
                    // No options available
                    if (this.showEmptyField) {
                        currentValue = 0;
                        options += '<option value="">' + this.msgNoRecords + '</options>';
                    }
                } else {
                    // Render the options
                    var lookupField = this.lookupField;
                    for (var i = 0; i < data.length; i++) {
                        if (i === 0) {
                            currentValue = data[i][lookupField];
                        }
                        options += '<option value="' + data[i][lookupField] + '">';
                        options += fncRepresent(data[i], prepResult);
                        options += '</option>';
                    }
                    if (this.optional) {
                        currentValue = 0;
                        options = '<option value=""></option>' + options;
                    }
                    if (this.currentValue) {
                        currentValue = this.currentValue;
                    }
                }

                var targetField = $('[name = "' + this.targetSelector + '"]');
                // Convert IS_ONE_OF_EMPTY INPUT to a SELECT
                var html = targetField.parent().html().replace('<input', '<select');
                targetField.parent().html(html);
                // reselect since it may have changed
                targetField = $('[name = "' + this.targetSelector + '"]');
                if (options !== '') {
                    targetField.html(options)
                               // Set the current field value
                               .val(currentValue)
                               .change()
                               .prop('disabled', false)
                               .show();
                } else {
                    // No options available => disable the target field
                    targetField.prop('disabled', true)
                               .show();
                }

                // Modify URL for Add-link and show the Add-link
                var lookupResource = this.lookupResource;
                var targetFieldAdd = $('#' + lookupResource + '_add');
                if (targetFieldAdd.length !== 0) {
                    var href = targetFieldAdd.attr('href');
                    triggerField = $('[name = "' + this.triggerSelector + '"]');
                    var triggerName = this.triggerName;
                    if (href.indexOf(triggerName) == -1) {
                        // Add to URL
                        href += '&' + triggerName + '=' + triggerField.val();
                    } else {
                        // Update URL
                        var re = new RegExp(triggerName + '=.*', 'g');
                        href = href.replace(re, triggerName + '=' + triggerField.val());
                    }
                    targetFieldAdd.attr('href', href).show();
                }

                // Remove the throbber
                $('#' + lookupResource + '_ajax_throbber').remove();
                if (first) {
                    // Don't include this change in the deliberate changes
                    S3ClearNavigateAwayConfirm();
                    first = false;
                }
            });
        } else {
            // URL returns the widget as HTML
            S3.JSONRequest[targetField.attr('id')] = $.ajax({
                url: url,
                dataType: 'html',
                context: context
            }).done(function(data) {
                var targetWidget = $('[name = "' + this.targetWidget + '"]');
                if (data !== '') {
                    // Replace the target field with the HTML returned
                    targetWidget.html(data)
                                .change()
                                .prop('disabled', false)
                                .show();
                } else {
                    // Disable the target field
                    targetWidget.prop('disabled', true);
                }
                // Remove Throbber
                $('#' + this.lookupResource + '_ajax_throbber').remove();
                if (first) {
                    // Don't include this change in the deliberate changes
                    S3ClearNavigateAwayConfirm();
                    first = false;
                }
            });
        }
    });

    // If the field value is empty - disable - but keep initial value
    triggerField.change();
}

// ============================================================================
/**
 * Add a Slider to a field - used by S3SliderWidget
 */
S3.slider = function(fieldname, minval, maxval, steprange, value) {
    $( '#' + fieldname ).slider({
        min: parseFloat(minval),
        max: parseFloat(maxval),
        step: parseFloat(steprange),
        value: parseFloat(value),
        slide: function (event, ui) {
            $( '#' + fieldname + '_input' ).val( ui.value );
        }
    });
};

// ============================================================================
/**
 * Reusable function to add a querystring variable to an existing URL and redirect into it.
 * It accounts for existing variables and will override an existing one.
 * Sample usage: _onchange="S3reloadWithQueryStringVars({'_language': $(this).val()});")
 */

function S3reloadWithQueryStringVars(queryStringVars) {
    var existingQueryVars = location.search ? location.search.substring(1).split("&") : [],
        currentUrl = location.search ? location.href.replace(location.search,"") : location.href,
        newQueryVars = {},
        newUrl = currentUrl + "?";
    if(existingQueryVars.length > 0) {
        for (var i = 0; i < existingQueryVars.length; i++) {
            var pair = existingQueryVars[i].split("=");
            newQueryVars[pair[0]] = pair[1];
        }
    }
    if(queryStringVars) {
        for (var queryStringVar in queryStringVars) {
            newQueryVars[queryStringVar] = queryStringVars[queryStringVar];
        }
    }
    if(newQueryVars) { 
        for (var newQueryVar in newQueryVars) {
            newUrl += newQueryVar + "=" + newQueryVars[newQueryVar] + "&";
        }
        newUrl = newUrl.substring(0, newUrl.length-1);
        window.location.href = newUrl;
    } else {
        window.location.href = location.href;
    }
}

// ============================================================================
