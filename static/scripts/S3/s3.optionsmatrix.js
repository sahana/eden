/*
 * This is used by S3OptionsMatrixWidget
 */

(function($) {
	var methods = {
		init: function(options) {
			return this.each(function() {
				//$(window).bind('resize.s3optionsmatrix', methods.reposition);
			});
		},
		destroy: function() {
			return this.each(function() {
			})
		},
		activateOptions: function(checklist) {
			// Check the checkboxes according to checklist
			alert(this)
		},
		replaceOptions: function(checklist) {
			// Uncheck all checkboxes before enabling those in checklist
			console.log(this)
		}
	};

	$.fn.s3optionsmatrix = function(method) {
		if(methods[method]) {
			return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
		} else if( typeof method === 'object' || !method) {
			return methods.init.apply(this, arguments);
		} else {
			$.error('Method ' + method + ' does not exist on s3optionsmatrix');
		}
	};
})(jQuery);
