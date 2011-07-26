/*
    site.js - Javascript containing the main site functions and effects.
                           
    License: GPLv3
    Copyright: 2011 Cidadania S. Coop. Galega
    Author: Oscar Carballal Prego <info@oscarcp.com>
*/

/* MESSAGES */

function msg() {
    // Show the messages slowly so the user can notice it.
    $("ul.messages").slideDown(2000);
    
    // On click "X" hide everything
    $(".closemsg").click(function (event) {
		// Prevent hyperlink to open the link with the default behaviour
		event.preventDefault();
		// Hide
		$("ul.messages").fadeOut('slow');
	});
}

function sitestart() {
    msg();
}

$(document).ready(function(){
    sitestart();
});


