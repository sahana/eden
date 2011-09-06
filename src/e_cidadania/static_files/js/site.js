/*
    site.js - Javascript containing the main site functions and effects.
                           
    License: GPLv3
    Copyright: 2011 Cidadania S. Coop. Galega
    Author: Oscar Carballal Prego <info@oscarcp.com>
*/

/* Cookie Reader (jQuery Cookie Plugin) */
$(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});

/* MESSAGES */

function checkBrowser() {
    // Detect IE 6-8
    if ( jQuery.support.leadingWhitespace == false ) {
        alert('Su navegador no dispone de las últimas tecnologías web.' +
            'Le recomendamos que se descargue Firefox, Google Chrome u Opera.')
    }
}

function msg() {
    // Show the messages slowly so the user can notice it.
    $("ul.messages").slideDown(2000);
    
    // On click "X" hide everything
    $(".closemsg").click(function (event) {
		// Prevent hyperlink to open the link with the default behaviour
		event.preventDefault();
		// Hide
		$("ul.messages").slideUp('slow');
	});
}

function sitestart() {
    msg();
}

$(document).ready(function(){
    checkBrowser();
    sitestart();
});


