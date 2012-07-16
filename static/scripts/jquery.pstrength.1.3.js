/* jQuery Password Strength Plugin (pstrength) - A jQuery plugin to provide accessibility functions
 * Author: Tane Piper (digitalspaghetti@gmail.com) 
 * Contributors: P. Andrews
 * Website: http://digitalspaghetti.me.uk
 * Licensed under the MIT License: http://www.opensource.org/licenses/mit-license.php
 * This code uses a modified version of Steve Moitozo's algorithm (http://www.geekwisdom.com/dyn/passwdmeter)
 * 
 * === Changelog ===
 * Version 1.3 (19/10/2007) P. Andrews (for spip plugin)
 *  added options for the too short and unsafe strings and colours
 *  use \W to match special characers
 *  remove 50 to the socre if the password contains a common word
 *  test that we don't have consecutive repetitions of at least 3 same alphanumerical.
 *  test that we have around the same numbers of num, alpha and letters.
 * Version 1.2 (03/09/2007)
 * Added more options for colors and common words
 * Added common words checked to see if words like 'password' or 'qwerty' are being entered
 * Added minimum characters required for password
 * Re-worked scoring system to give better results
 * 
 * Version 1.1 (20/08/2007)
 * Changed code to be more jQuery-like
 * 
 * Version 1.0 (20/07/2007)
 * Initial version.
 */
(function($){
	$.extend($.fn, {
		pstrength : function(options) {
			var options = $.extend({
				verdects:	["Very Weak","Weak","Medium","Strong","Very Strong","Too Short","Unsafe Password Word!"],
				colors: 	["#f00","#c06", "#f60","#3c0","#3f0","#ccc","#f00"],
				scores: 	[10,15,30,40],
				common:		["password","sex","god","123456","123","liverpool","letmein","qwerty","monkey"],
				minchar:	6,
				minchar_label:   "The minimum number of characters is "
			},options);		
			return this.each(function(){
				var infoarea = $(this).attr('id');
				$(this).after('<div class="pstrength-minchar" id="' + infoarea + '_minchar">'+options.minchar_label + options.minchar + '</div>');
				$(this).after('<div class="pstrength-info" id="' + infoarea + '_text"></div>');
				$(this).after('<div class="pstrength-bar" id="' + infoarea + '_bar" style="border: 1px solid white; font-size: 1px; height: 2px; width: 0px;"></div>');
				$(this).keyup(function(){				
					$.fn.runPassword($(this).val(), infoarea, options);
				});
			});
		},
		runPassword : function (password, infoarea, options){
			// Check password
			nPerc = $.fn.checkPassword(password, options);
			// Get controls
	    	var ctlBar = "#" + infoarea + "_bar"; 
	    	var ctlText = "#" + infoarea + "_text";		
			// Color and text
			//contains compound, too simple
			if (nPerc <= -200) {
				strColor = options.colors[6];
				strText = options.verdects[6];
				$(ctlBar).css({width: "0%"});
			}		
			//too short
			else if (nPerc <= 0 && nPerc >= -199) {
				strColor = options.colors[5];
				strText = options.verdects[5];
				$(ctlBar).css({width: "1%"});
			}
			else if(nPerc >= 0 && nPerc <= options.scores[0])
			{
		   		strColor = options.colors[0];
				strText = options.verdects[0];
				$(ctlBar).css({width: "1%"});
			}
			else if (nPerc > options.scores[0] && nPerc <= options.scores[1])
			{
		   		strColor = options.colors[1];
				strText = options.verdects[1];
				$(ctlBar).css({width: "25%"});
			}
			else if (nPerc > options.scores[1] && nPerc <= options.scores[2])
			{
			   	strColor = options.colors[2];
				strText = options.verdects[2];
				$(ctlBar).css({width: "50%"});
			}
			else if (nPerc > options.scores[2] && nPerc <= options.scores[3])
			{
			   	strColor = options.colors[3];
				strText = options.verdects[3];
				$(ctlBar).css({width: "75%"});
			}
			else
			{
			   	strColor = options.colors[4];
				strText = options.verdects[4];
				$(ctlBar).css({width: "99%"});
			}
			$(ctlBar).css({backgroundColor: strColor});
			$(ctlText).html("<span style='color: " + strColor + ";'>" + strText + "</span>");
		},
		checkPassword : function(password, options)
		{
			var intScore = 0;
			var strVerdict = options.verdects[0];	
			// PASSWORD LENGTH
			if (password.length < options.minchar)                         // Password too short
			{
				intScore = (intScore - 100)
			}
			else if (password.length >= options.minchar && password.length <= (options.minchar + 2)) // Password Short
			{
				intScore = (intScore + 6)
			}
			else if (password.length >= (options.minchar + 3) && password.length <= (options.minchar + 4))// Password Medium
			{
				intScore = (intScore + 12)
			}
			else if (password.length >= (options.minchar + 5))                    // Password Large
			{
				intScore = (intScore + 18)
			}
			if (password.match(/[a-z]/))                              // [verified] at least one lower case letter
			{
				intScore = (intScore + 1)
			}
			if (password.match(/[A-Z]/))                              // [verified] at least one upper case letter
			{
				intScore = (intScore + 5)
			}
			// NUMBERS
			if (password.match(/\d+/))                                 // [verified] at least one number
			{
				intScore = (intScore + 5)
			}
			if (password.match(/(.*[0-9].*[0-9].*[0-9])/))             // [verified] at least three numbers
			{
				intScore = (intScore + 7)
			}
			// SPECIAL CHAR
			if (password.match(/.\W/))            // [verified] at least one special character
			{
				intScore = (intScore + 5)
			}
			// [verified] at least two special characters
			if (password.match(/(.*\W.*\W)/))
			{
				intScore = (intScore + 7)
			}
			// COMBOS
			if (password.match(/([a-z].*[A-Z])|([A-Z].*[a-z])/))        // [verified] both upper and lower case
			{
				intScore = (intScore + 2)
			}
			if (password.match(/([a-zA-Z])/) && password.match(/([0-9])/)) // [verified] both letters and numbers
			{
				intScore = (intScore + 3)
			}
		 	// [verified] letters, numbers, and special characters
			if (password.match(/([a-zA-Z0-9].*\W)|(\W.*[a-zA-Z0-9])/))
			{
				intScore = (intScore + 3)
			}
			// the password contains a chain of 3 identical alphanumeric character (aaaXk, bbbbbb19, ...)
			if(password.match(/(\w)\1{2}/)) {
				intScore -= 10;
			}	
			// the password contains a chain of 4 alpha letters... decrease the strength
			if(password.match(/[a-z]{4}/i)) {
				intScore -= 5;
			}				
			//check out the ratio between alpha, numerical and special chars:
			var split = password.split(/\d/);
			var cnt_num = split.length-1;
			split = password.split(/\W/);
			var cnt_special = split.length-1;
			var cnt_alpha = password.length-cnt_alpha-cnt_special;
			var diff_alphanum = cnt_alpha-cnt_num;
			if(diff_alphanum <= password.length/3 || diff_alphanum >= -password.length/3) {
				intScore += 7;
			}
			var diff_alphaspecial = cnt_alpha-cnt_special;
			if(diff_alphaspecial <= password.length/3 || diff_alphaspecial >= -password.length/3) {
				intScore += 7;
			}
			for (var i=0; i < options.common.length; i++) {
				//check that the password doesn't contain a common word
				if (password.toLowerCase() == options.common[i]) {
					intScore = -200;
				} else if (password.toLowerCase().indexOf(options.common[i]) >= 0) {
					intScore -= 20;
				}
			}
			return intScore;
		}
	});
})(jQuery);
