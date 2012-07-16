/*
 *  jCollapsible - Makes any nested list collapsible by adding an icon to the left of it
 *  Copyright 2010 Monjurul Dolon, http://mdolon.com/
 *  Released under the MIT, BSD, and GPL Licenses.
 *  More information: http://devgrow.com/simple-threaded-comments-with-jcollapsible
 */
$.fn.collapsible = function(options) {
	var defaults = {defaulthide: true, symbolhide: '-', symbolshow: '+', imagehide: null, imageshow: null, xoffset: '-15', yoffset: '0'};
	var opts = $.extend(defaults, options); var o = $.meta ? $.extend({}, opts, $$.data()) : opts; var obj = $(this);
	if(o.imageshow) o.symbolshow = '<img src="'+o.imageshow+'" class="jc-show" border="0">';
	if(o.imagehide) o.symbolhide = '<img src="'+o.imagehide+'" class="jc-hide" border="0">';
	var startsymbol = o.symbolshow;
	$('li', obj).each(function(index) {
		if($('>ul, >ol',this).size() > 0){
			if(o.defaulthide) $('>ul, >ol',this).hide(); else startsymbol = o.symbolhide;
			$(this).prepend('<a href="" class="jcollapsible" style="position:absolute;outline:0;left:'+o.xoffset+'px;top:'+o.yoffset+'px;">'+startsymbol+'</a>').css('position','relative');
		}
	});
	$('.jcollapsible', obj).click(function(){
		var parent = $(this).parent();
		$('>ul, >ol',parent).slideToggle('fast');
		$(this).html($(this).html() == o.symbolshow ? o.symbolhide : o.symbolshow);
		return false;
	});
};