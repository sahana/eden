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
function openPopup(url) {
    if ( !popupWin || popupWin.closed ) {
        popupWin = window.open(url, 'popupWin', 'width=640, height=480');
    } else popupWin.focus();
}
$(document).ready(function() {
    // Web2Py Layer
    $('.error').hide().slideDown('slow')
    $('.error').click(function() { $(this).fadeOut('slow'); return false; });
    $('.warning').hide().slideDown('slow')
    $('.warning').click(function() { $(this).fadeOut('slow'); return false; });
    $('.information').hide().slideDown('slow')
    $('.information').click(function() { $(this).fadeOut('slow'); return false; });
    $('.confirmation').hide().slideDown('slow')
    $('.confirmation').click(function() { $(this).fadeOut('slow'); return false; });
    $("input[type='checkbox'].delete").click(function() { if(this.checked) if(!confirm(S3.i18n.delete_confirmation)) this.checked=false; });
    try { $('input.datetime').focus( function() {
        Calendar.setup({
            inputField: this.id, ifFormat: S3.i18n.datetime_format, showsTime: true, timeFormat: '24'
        });
    }); } catch(e) {};

    // T2 Layer
    try { $('.zoom').fancyZoom( {
        scaleImg: true,
        closeOnClick: true,
        directory: S3.Ap.concat("/static/media")
    }); } catch(e) {};

    // S3 Layer
    // dataTables' delete button
    // (can't use S3ConfirmClick as the buttons haven't yet rendered)
    if (S3.interactive) {
        $('a.delete-btn').live('click', function(event) {
            if (confirm(S3.i18n.delete_confirmation)) {
                return true;
            } else {
                event.preventDefault();
                return false;
            }
        });
    }

    // Datepicker
    $('input.date').datepicker({
        changeMonth: true, changeYear: true,
        //showOtherMonths: true, selectOtherMonths: true,
        showOn: 'both',
        buttonImage: S3.Ap.concat('/static/img/jquery-ui/calendar.gif'),
        buttonImageOnly: true,
        dateFormat: 'yy-mm-dd',
        isRTL: S3.rtl
     });

    $('input.time').timepicker({
        hourText: S3.i18n.hour,
        minuteText: S3.i18n.minute,
        defaultTime: ''
    });

    // accept comma as thousands separator
    $('input.int_amount').keyup(function(){this.value=this.value.reverse().replace(/[^0-9\-,]|\-(?=.)/g,'').reverse();});
    $('input.float_amount').keyup(function(){this.value=this.value.reverse().replace(/[^0-9\-\.,]|[\-](?=.)|[\.](?=[0-9]*[\.])/g,'').reverse();});

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

    /*
    // unused in new sidebar subnav
    $('#subnav li').hover(
        function() {
                var popup_width = $(this).width()-2;
                $('ul', this).css({
                    'display': 'block',
                    'width': popup_width.toString() + 'px'
                });
            },
        function() { $('ul', this).css('display', 'none');  }
    );
    */

    // Colorbox Popups
    $('a.colorbox').attr('href', function(index, attr) {
        // Add the caller to the URL vars so that the popup knows which field to refresh/set
        var caller = '';
        try {
            caller = $(this).parents('tr').attr('id').replace(/__row/, '');
        } catch(e) {
            // Do nothing
            if(caller == '') return attr;
        }
        // Avoid Duplicate callers
        var url_out = attr;
        if (attr.indexOf('&caller=') == -1){
            url_out = attr + '&caller=' + caller;
        }
        return url_out;
    });
    $('.colorbox').click(function(){
        $.fn.colorbox({iframe:true, width:'99%', height:'99%', href:this.href, title:this.title});
        return false;
    });

    // Help Tooltips
    $('.tooltip').cluetip({activation: 'hover', sticky: false, splitTitle: '|'});
    $('.tooltipbody').cluetip({activation: 'hover', sticky: false, splitTitle: '|', showTitle: false});
    var tipCloseText = '<img src="' + S3.Ap.concat('/static/img/cross2.png') + '" alt="close" />';
    $('.stickytip').cluetip( {
    	activation: 'hover',
    	sticky: true,
    	closePosition: 'title',
    	closeText: tipCloseText,
    	splitTitle: '|'
    } );
    $('.errortip').cluetip( {
        activation: 'click',
        sticky: true,
        closePosition: 'title',
        closeText: tipCloseText,
        splitTitle: '|'
    } );
    $('.ajaxtip').cluetip( {
    	activation: 'click',
    	sticky: true,
    	closePosition: 'title',
    	closeText: tipCloseText,
    	width: 380
    } );
    now = new Date();
    $('form').append("<input type='hidden' value=" + now.getTimezoneOffset() + " name='_utc_offset'/>");
	
	// Social Media 'share' buttons
    if ($('#socialmedia_share').length > 0) {
        // DIV exists (deployment_setting on)
        var currenturl = document.location.href;
        var currenttitle = document.title;
        // Facebook
        $('#socialmedia_share').append("<div class='socialmedia_element'><div id='fb-root'></div><script>(function(d, s, id) { var js, fjs = d.getElementsByTagName(s)[0]; if (d.getElementById(id)) return; js = d.createElement(s); js.id = id; js.src = '//connect.facebook.net/en_US/all.js#xfbml=1'; fjs.parentNode.insertBefore(js, fjs); }(document, 'script', 'facebook-jssdk'));</script> <div class='fb-send' data-href='" + currenturl + "'></div></div>");
        // Twitter
        $('#socialmedia_share').append("<div class='socialmedia_element'><a href='https://twitter.com/share' class='twitter-share-button' data-count='none' data-hashtags='sahana-eden'>Tweet</a><script>!function(d,s,id){var js,fjs=d.getElementsByTagName(s)[0];if(!d.getElementById(id)){js=d.createElement(s);js.id=id;js.src='//platform.twitter.com/widgets.js';fjs.parentNode.insertBefore(js,fjs);}}(document,'script','twitter-wjs');</script></div>");
    }
});

function s3_tb_remove(){
    // Colorbox Popup
    $.fn.colorbox.close();
}

// ============================================================================
// @author: Michael Howden (michael@sahanafoundation.org)
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
// @author: Michael Howden (michael@sahanafoundation.org)
function S3SetNavigateAwayConfirm() {
    window.onbeforeunload = function() {
        return S3.i18n.unsaved_changes;
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
            s3_showStatus(S3.i18n.ajax_get + ' ' + (s.message ? s.message : S3.i18n.ajax_fmd) + '...', this.ajaxS3Settings.msgTimeout);
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
                    s3_showStatus(S3.i18n.ajax_get + ' ' + (s.message ? s.message : S3.i18n.ajax_fmd) + '... ' + S3.i18n.ajax_rtr + ' ' + this.tryCount,
                        $.ajaxS3Settings.msgTimeout);
                    $.ajax(this);
                    return;
                }
                s3_showStatus(S3.i18n.ajax_wht + ' ' + (this.retryLimit + 1) + ' ' + S3.i18n.ajax_gvn,
                    $.ajaxS3Settings.msgTimeout, false, true);
                return;
            }
            if (xhr.status == 500) {
                s3_showStatus(S3.i18n.ajax_500, $.ajaxS3Settings.msgTimeout, false, true);
            } else {
                s3_showStatus(S3.i18n.ajax_dwn, $.ajaxS3Settings.msgTimeout, false, true);
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
    var closelink = $('<a href=\"#\">' + S3.i18n.close_map + '</a>');

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
    var closelink = $('<a href=\"#\">' + S3.i18n.close_map + '</a>');

    // @ToDo: Also make the represent link act as a close
    closelink.bind( 'click', function(evt) {
        $('#map').html(oldhtml);
        evt.preventDefault();
    });

    $('#map').html(iframe);
    $('#map').append($("<div style='margin-bottom: 10px' />").append(closelink));
}

// ============================================================================
/**
 * Re-usable function to filter a select field based on a "filter field", eg:
 * Rooms filtered by Site
 * Item Packs filtered by Item
 * Competency Ratings filtered by Skill Type
 * @ToDo: - Ensure that the automatically set value of the select field
 * 			doesn't activate the "NavigateAwayConfirm"
 */
function S3FilterFieldChange (setting) {
	/**
     * Sets a Field to be hidden until a FilterField is set,
	 * then filters it's options according to that filter field
	 *
	 * @param: Field
	 * @param: FilterField
	 * @param: FieldPrefix
	 * @param: FieldResource
	 * @param: FieldKey			(optional) The key field in the filter (parent) resource
	 * 							default: FilterField
	 * @param: FieldID			(optional) The ID field in the resource the field refers to
	 * 							default: "id"
	 * @param: url				(optional) URL to get filtered options for the Field
	 * 							default:	S3.Ap.concat('/', FieldPrefix, '/', FieldResource, '.json?',
	    									FieldResource, '.',  FilterField, '=' )
	 * @param: ShowEmptyField	(optional) Is the Field displayed if there are no valid options
	 * 							default: true
	 * @param: msgNoRecords		(optional)
	 * @param: fncPrep			(optional) Pre-Processes the data returned. Returns PrepResult
	 * 							default: function(data) {return null}
	 * @param: fncRepresent		(optional) Represents the data returned for the Field option
	 * 							default: function(record, PrepResult) {return record.name}
	 */

	// Check if this field is present in this page
	var FilterField = setting.FilterField;
    var selFilterField = $('[name = "' + FilterField + '"]');
    if ( undefined == selFilterField[0] ) {
        return
    }

	var Field = setting.Field;
    var selField = $('[name = "' + Field + '"]');
    //var selFieldRows = $('[id *= "' + Field + '__row"]');

    selFilterField.change( function() {

	    // Cancel previous request
	    try {
            S3.JSONRequest[$(this).attr('id')].abort();
        } catch(err) {};

	    if (selFilterField.val() == "" || selFilterField.val() == undefined) {
	    	// No value to filter
	    	//selFieldRows.hide();
	    	selField.attr('disabled', 'disabled');
	        return;
	    }

		var FieldResource = setting.FieldResource;

		if (setting.FieldKey != undefined) {
			var FieldKey = setting.FieldKey;
		} else {
			var FieldKey = FilterField;
	    }

		var FieldID = setting.FieldID;
		if (FieldID == undefined) {
			var FieldID = "id";
		}

	    if (setting.url  != undefined && setting.url  != null) {
	    	var url = setting.url
	    } else {
	    	var FieldPrefix = setting.FieldPrefix;
	    	var url = S3.Ap.concat('/', FieldPrefix, '/', FieldResource, '.json?',
	    							FieldResource, '.',  FieldKey, '=' );
	    }
	    url = url.concat(selFilterField.val())
		if (setting.ShowEmptyField != undefined) {
			var ShowEmptyField = setting.ShowEmptyField;
		} else {
			var ShowEmptyField = true;
	    }
		if (setting.msgNoRecords != undefined) {
			var msgNoRecords = setting.msgNoRecords;
		} else {
			var msgNoRecords = '-';
			setting.msgNoRecords = msgNoRecords;
		}
		if (setting.fncPrep != undefined) {
			var fncPrep = setting.fncPrep;
		} else {
			var fncPrep = function(data) {return null};
			setting.fncPrep = fncPrep;
	    }
		if (setting.fncRepresent != undefined) {
			var fncRepresent = setting.fncRepresent;
		} else {
			var fncRepresent = function(record) {return record.name};
			setting.fncRepresent = fncRepresent;
	    }

		//if ($('[id$="' + FilterField + '__row1"]:visible').length > 0) {
			// Only show if the filter field is shown
			//selFieldRows.show();
		//}

	    /* Show Throbber */
	    selField.hide();
	    if ($('#' + FieldResource + '_ajax_throbber').length == 0 ) {
	        selField.after('<div id="' + FieldResource + '_ajax_throbber" class="ajax_throbber"/>')
	    }

	    var data;

	    // Save JSON Request by element id
	    S3.JSONRequest[$(this).attr('id')] = $.ajax( {
	        url: url,
	        dataType: 'json',
	        context: setting,
	        success: function(data) {
	        /* Create Select Element */
	            var options = '';
	            var FilterField = this.FilterField;
	            var FieldResource = this.FieldResource;
	            var selField = $('[name = "' + this.Field + '"]');
	            var selFilterField = $('[name = "' + FilterField + '"]');

	            PrepResult = fncPrep(data);

	            if (data.length == 0) {
	            	if (ShowEmptyField) {
	            		var first_value = 0;
		                options += '<option value="">' + this.msgNoRecords + '</options>';
	            	}
	            } else {
	                for (var i = 0; i < data.length; i++) {
	                	if (i == 0) {first_value = data[i][FieldID]};
	                    options += '<option value="' +  data[i][FieldID] + '">';
	                    options += this.fncRepresent( data[i], this.PrepResult);
	                    options += '</option>';
	                }
	            }
	            /* Set field value */
	            if (options != '') {
		            selField.html(options)
                    .val(first_value)
                    .change()
                    .removeAttr('disabled')
                    .show();
	            } else {
	            	//selFieldRows.hide();
	            	selField.attr('disabled', 'disabled');
	            }
	            /* Show "Add" Button & modify link */
	            selFieldAdd = $('#' + FieldResource + '_add')
	            href = selFieldAdd.attr('href') + "&' + FilterField + '=" + $('[name = "' + FilterField + '"]').val();
	            selFieldAdd.attr('href', href)
	                       .show();

	            /* Remove Throbber */
	            $('#' + FieldResource + '_ajax_throbber').remove();
	        }
	    });
    });
    // Initially hide or filter field
    selFilterField.change();
};
// ============================================================================