/*
    site.js - Javascript containing the main site functions and effects.
                           
    License: GPLv3
    Copyright: 2011 Cidadania S. Coop. Galega
    Author: Oscar Carballal Prego <info@oscarcp.com>
*/

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


