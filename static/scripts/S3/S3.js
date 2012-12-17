/**
 * Custom Javascript functions added as part of the S3 Framework
 * Strings are localised in views/l10n.js
 */

// Global variable to store all of our variables inside
var S3 = Object();
S3.gis = Object();
S3.timeline = Object();
S3.JSONRequest = Object(); // Used to store and abort JSON requests
S3.TimeoutVar = Object(); // Used to store and abort JSON requests

S3.uid = function () {
    // Generate a random uid
    // Used by GIS
    // http://jsperf.com/random-uuid/2
    return (((+(new Date())) / 1000 * 0x10000 + Math.random() * 0xffff) >> 0).toString(16);
}

S3.Utf8 = {
    // Used by dataTables
    // http://www.webtoolkit.info
    encode: function (string) {
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
    decode: function (utftext) {
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
}

// Used by Scenario module currently, but may be deprecated as not great UI
var popupWin = null;
// function openPopup(url) {
    // if ( !popupWin || popupWin.closed ) {
        // popupWin = window.open(url, 'popupWin', 'width=640, height=480');
    // } else popupWin.focus();
// }
function openPopup(url, center) {
    if ( !popupWin || popupWin.closed ) {
        var params = 'width=640, height=480';
        if (center == true) {
            params += ',left=' + (screen.width - 640)/2 +
                ',top=' + (screen.height - 480)/2;
        }
        popupWin = window.open(url, 'popupWin', params);
    } else popupWin.focus();
}
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
}

$(document).ready(function() {
    // Web2Py Layer
    $('.error').hide().slideDown('slow');
    $('.error').click(function() { $(this).fadeOut('slow'); return false; });
    $('.warning').hide().slideDown('slow')
    $('.warning').click(function() { $(this).fadeOut('slow'); return false; });
    $('.information').hide().slideDown('slow')
    $('.information').click(function() { $(this).fadeOut('slow'); return false; });
    $('.confirmation').hide().slideDown('slow')
    $('.confirmation').click(function() { $(this).fadeOut('slow'); return false; });
    $("input[type='checkbox'].delete").click(function() {
        if ((this.checked) && (!confirm(i18n.delete_confirmation))) {
                this.checked=false;
        }
    });

    // If a form is submitted with errors, this will scroll
    // the window to the first form error message
    inputErrorId = $('form .error[id]').eq(0).attr('id');
    if (inputErrorId != undefined) {
        inputName = inputErrorId.replace('__error', '');
        inputId = $('[name=' + inputName + ']').attr('id');
        inputLabel = $('[for=' + inputId + ']');
        window.scrollTo(0, inputLabel.offset().top)
    }

    // T2 Layer
    //try { $('.zoom').fancyZoom( {
    //    scaleImg: true,
    //    closeOnClick: true,
    //    directory: S3.Ap.concat('/static/media')
    //}); } catch(e) {};

    // S3 Layer
    // dataTables' delete button
    // (can't use S3ConfirmClick as the buttons haven't yet rendered)
    if (S3.interactive) {
        $('a.delete-btn').live('click', function(event) {
            if (confirm(i18n.delete_confirmation)) {
                return true;
            } else {
                event.preventDefault();
                return false;
            }
        });
        $('input:text:visible:first').focus();
    }

    // Accept comma as thousands separator
    $('input.int_amount').keyup(function(){this.value=this.value.reverse().replace(/[^0-9\-,]|\-(?=.)/g,'').reverse();});
    $('input.float_amount').keyup(function(){this.value=this.value.reverse().replace(/[^0-9\-\.,]|[\-](?=.)|[\.](?=[0-9]*[\.])/g,'').reverse();});
    // Auto-capitalize first names
    $('input[name="first_name"]').focusout(function() {this.value = this.value.charAt(0).toLocaleUpperCase() + this.value.substring(1);})
    // Hide password verification field in admin/user until changed
    $('input[name="password"]').keyup(function() {
        $('.verify-password').removeClass('hide');
        $('#password_two').removeAttr('disabled');
    });

    // Resizable textareas
    $('textarea.resizable:not(.textarea-processed)').each(function() {
        // Avoid non-processed teasers.
        if ($(this).is(('textarea.teaser:not(.teaser-processed)'))) {
            return false;
        }
        var textarea = $(this).addClass('textarea-processed');
        var staticOffset = null;
        // When wrapping the text area, work around an IE margin bug. See:
        // http://jaspan.com/ie-inherited-margin-bug-form-elements-and-haslayout
        $(this).wrap('<div class="resizable-textarea"><span></span></div>')
        .parent().append($('<div class="grippie"></div>').mousedown(startDrag));
        var grippie = $('div.grippie', $(this).parent())[0];
        grippie.style.marginRight = (grippie.offsetWidth - $(this)[0].offsetWidth) + 'px';
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
    });

    // IE6 non anchor hover hack
    $('#modulenav .hoverable').hover(
        function() { $(this).addClass('hovered'); },
        function() { $(this).removeClass('hovered'); }
    );

    // Menu popups (works in IE6)
    $('#modulenav li').hover(
        function() {
                var header_width = $(this).width();
                var popup_width = $('ul', this).width();
                if (popup_width != null){
                  if (popup_width < header_width){
                    $('ul', this).css({
                        'width': header_width.toString() + 'px'
                    });
                  }
                }
                $('ul', this).css('display', 'block');
            },
        function() { $('ul', this).css('display', 'none');  }
    );

    // Colorbox Popups
    $('a.colorbox').attr('href', function(index, attr) {
        // Add the caller to the URL vars so that the popup knows which field to refresh/set
        var caller = $(this).parents('tr').attr('id');
        if (!caller) {
            // DIV-based formstyle
            caller = $(this).parent().parent().attr('id');
        }
        caller = caller.replace(/__row/, '');
        // Avoid Duplicate callers
        var url_out = attr;
        if (attr.indexOf('caller=') == -1) {
            url_out = attr + '&caller=' + caller;
        }
        return url_out;
    });
    $('.colorbox').click(function() {
        $.fn.colorbox({
            iframe: true,
            width: '99%',
            height: '99%',
            href: this.href,
            title: this.title
        });
        return false;
    });

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

function s3_tb_remove(){
    // Colorbox Popup
    $.fn.colorbox.close();
}

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
                success: function(data) {
                    $('.mark-deduplicate, .unmark-deduplicate, .deduplicate').toggleClass('hide');
                    return;
                },
                dataType: 'JSON'
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
                success: function(data) {
                    $('.mark-deduplicate, .unmark-deduplicate, .deduplicate').toggleClass('hide');
                    return;
                },
                dataType: 'JSON'
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
}

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
};

// ============================================================================
// Code to warn on exit without saving
function S3SetNavigateAwayConfirm() {
    window.onbeforeunload = function() {
        return i18n.unsaved_changes;
    };
};

function S3ClearNavigateAwayConfirm() {
    window.onbeforeunload = function() {};
};

function S3EnableNavigateAwayConfirm() {
    $(document).ready(function() {
        if ( $('[class=error]').length > 0 ) {
            // If there are errors, ensure the unsaved form is still protected
            S3SetNavigateAwayConfirm();
        }
        $(':input:not(input[id=gis_location_advanced_checkbox])').keypress( S3SetNavigateAwayConfirm );
        $(':input:not(input[id=gis_location_advanced_checkbox])').change( S3SetNavigateAwayConfirm );
        $('form').submit( S3ClearNavigateAwayConfirm );
    });
};

// ============================================================================
/**
 * ajaxS3
 * added by sunneach 2010-feb-14
 */

(function($) {
    $.ajaxS3 = function(s) {
        var options = $.extend( {}, $.ajaxS3Settings, s );
        options.tryCount = 0;
        if (s.message) {
            s3_showStatus(i18n.ajax_get + ' ' + (s.message ? s.message : i18n.ajax_fmd) + '...', this.ajaxS3Settings.msgTimeout);
        }
        options.success = function(data, status) {
            s3_hideStatus();
            if (s.success)
                s.success(data, status);
        }
        options.error = function(xhr, textStatus, errorThrown ) {
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
                return;
            }
            if (xhr.status == 500) {
                s3_showStatus(i18n.ajax_500, $.ajaxS3Settings.msgTimeout, false, true);
            } else {
                s3_showStatus(i18n.ajax_dwn, $.ajaxS3Settings.msgTimeout, false, true);
            }
        };
        $.ajax(options);
    };

    $.postS3 = function(url, data, callback, type) {
        return $.ajaxS3({
            type: "POST",
            url: url,
            data: data,
            success: callback,
            dataType: type
        });
    };

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
            success: callback,
            dataType: type,
            message: message
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
            var sync = false;
        }
        return $.getS3(url, data, callback, 'json', message, sync);
    };

    $.ajaxS3Settings = {
        timeout : 10000,
        msgTimeout: 2000,
        retryLimit : 10,
        dataType: 'json',
        async: true,
        type: 'GET'
    };

    $.ajaxS3Setup = function(settings) {
        $.extend($.ajaxS3Settings, settings);
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
    }
    this.release = function() {
        if (_statusbar) {
            $('#_statusbar').remove();
            _statusbar = undefined;
        }
    }
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
    openPopup(url, true);
}

// ============================================================================
/**
 * Re-usable function to filter a select field based on a "filter field", eg:
 * Rooms filtered by Site
 * Item Packs filtered by Item
 * Competency Ratings filtered by Skill Type
 **/

function S3OptionsFilter(settings) {
    /**
     * New version of S3FilterFieldChange that works both with regular
     * as well as with inline forms.
     *
     * @todo: migrate all use-cases to this version
     *
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

    var triggerName = settings.triggerName
    var targetName = settings.targetName

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
        } catch(err) {};

        // Get the lookup value from the trigger field
        var lookupValue = '';
        if (triggerField.length == 1) {
            // SELECT
            lookupValue = triggerField.val();
        } else if (triggerField.length > 1) {
            // Checkboxes
            lookupValue = new Array();
            triggerField.filter('input:checked').each(function() {
                lookupValue.push($(this).val());
            });
        }

        // Disable the target field if no value selected
        if (lookupValue == '' || lookupValue === undefined) {
            targetField.attr('disabled', 'disabled');
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
        if (settings.lookupURL) {
            var url = settings.lookupURL;
            if (lookupValue) {
                url = url.concat(lookupValue);
            }
        } else {
            var lookupPrefix = settings.lookupPrefix;
            var url = S3.Ap.concat('/', lookupPrefix, '/', lookupResource, '.json');
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
            context['fncPrep'] = function(data) { return null };
        }
        if (settings.fncRepresent) {
            context['fncRepresent'] = settings.fncRepresent;
        } else {
            context['fncRepresent'] = function(record) { return record.name };
        }

        // Find the target widget and replace it by a throbber
        if (settings.targetWidget != undefined) {
            var targetWidget = settings.targetWidget;
        } else {
            var targetWidget = targetSelector;
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
                context: context,
                success: function(data) {

                    // Pre-process the data
                    var fncPrep = this.fncPrep;
                    try {
                        var prepResult = fncPrep(data);
                    } catch (e) {
                        var prepResult = null;
                    };

                    // Render options list
                    var fncRepresent = this.fncRepresent;
                    var FilterField = this.FilterField;
                    var FieldResource = this.FieldResource;
                    var triggerField = $('[name = "' + FilterField + '"]');
                    var options = '';
                    if (data.length === 0) {
                        // No options available
                        if (this.showEmptyField) {
                            var currentValue = 0;
                            options += '<option value="">' + this.msgNoRecords + '</options>';
                        }
                    } else {
                        // Render the options
                        var lookupField = this.lookupField
                        for (var i = 0; i < data.length; i++) {
                            if (i == 0) {
                                var currentValue = data[i][lookupField];
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

                    // Set the current field value
                    var targetField = $('[name = "' + this.targetSelector + '"]');
                    if (options != '') {
                        targetField.html(options)
                                   .val(currentValue)
                                   .change()
                                   .removeAttr('disabled')
                                   .show();
                    } else {
                        // No options available => disable the target field
                        targetField.attr('disabled', 'disabled')
                                   .show();
                    }

                    // Modify URL for Add-link and show the Add-link
                    var lookupResource = this.lookupResource;
                    var targetFieldAdd = $('#' + lookupResource + '_add');
                    if (targetFieldAdd.length !== 0) {
                        var href = targetFieldAdd.attr('href');
                        var triggerField = $('[name = "' + this.triggerSelector + '"]');
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
                }
            });
        } else {
            // URL returns the widget as HTML
            S3.JSONRequest[targetField.attr('id')] = $.ajax({
                url: url,
                dataType: 'html',
                context: context,
                success: function(data) {
                    var targetWidget = $('[name = "' + this.targetWidget + '"]');
                    if (data != '') {
                        // Replace the target field with the HTML returned
                        targetWidget.html(data)
                                    .change()
                                    .removeAttr('disabled')
                                    .show();
                    } else {
                        // Disable the target field
                        targetWidget.attr('disabled', 'disabled');
                    }
                    // Remove Throbber
                    $('#' + this.lookupResource + '_ajax_throbber').remove();
                    if (first) {
                        // Don't include this change in the deliberate changes
                        S3ClearNavigateAwayConfirm();
                        first = false;
                    }
                }
            });

        }
    });

    // If the field value is empty - disable - but keep initial value
    triggerField.change();
};

// ============================================================================
/**
 * Add an Autocomplete to a field - used by S3AutocompleteWidget
 */

S3.autocomplete = function(fieldname, module, resourcename, input, filter, link, postprocess, delay, min_length) {
    var real_input = '#' + input;
    var dummy = 'dummy_' + input;
    var dummy_input = '#' + dummy;

    if ($(dummy_input) == 'undefined') {
        return true;
    }

    var url = S3.Ap.concat('/', module, '/', resourcename, '/search.json?filter=~&field=', fieldname);
    if (filter != 'undefined') {
        url += '&' + filter;
    }
    if ((link == 'undefined') || (link == '')) {
        // pass
    } else {
        url += '&link=' + link;
    }

    // Optional args
    if (postprocess == 'undefined') {
        var postprocess = '';
    }
    if (delay == 'undefined') {
        var delay = 450;
    }
    if (min_length == 'undefined') {
        var min_length = 2;
    }
    var data = {
        val: $(dummy_input).val(),
        accept: false
    };
    $(dummy_input).autocomplete({
        source: url,
        delay: delay,
        minLength: min_length,
        search: function(event, ui) {
            $( '#' + dummy + '_throbber' ).removeClass('hide').show();
            return true;
        },
        response: function(event, ui, content) {
            $( '#' + dummy + '_throbber' ).hide();
            return content;
        },
        focus: function( event, ui ) {
            $( dummy_input ).val( ui.item[fieldname] );
            return false;
        },
        select: function( event, ui ) {
            $( dummy_input ).val( ui.item[fieldname] );
            $( real_input ).val( ui.item.id );
            $( real_input ).change();
            if (postprocess) {
                eval(postprocess);
            }
            data.accept = true;
            return false;
        }
    })
    .data( 'autocomplete' )._renderItem = function( ul, item ) {
        return $( '<li></li>' )
            .data( 'item.autocomplete', item )
            .append( '<a>' + item[fieldname] + '</a>' )
            .appendTo( ul );
    };
    // @ToDo: Do this only if new_items=False
    $(dummy_input).blur(function() {
        if (!$(dummy_input).val()) {
            $(real_input).val('');
            data.accept = true;
        }
        if (!data.accept) {
            $(dummy_input).val(data.val);
        } else {
            data.val = $(dummy_input).val();
        }
        data.accept = false;
    });
};

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
