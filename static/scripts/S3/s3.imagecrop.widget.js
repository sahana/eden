$(function () {
	/* NOTE: Keep this in sync with s3.IMAGE_EXTENSIONS from 00_settings.py */
	var IMAGE_EXTENSIONS = ["png", "PNG", "jpg", "JPG", "jpeg", "JPEG", "gif", "GIF", "tif", "TIF", "tiff", "TIFF", "bmp", "BMP", "raw", "RAW"];
	
	function isValidImagePath(path) {
		var extension = path.split(".");
		extension = extension[extension.length - 1];
		
		return $.inArray(extension, IMAGE_EXTENSIONS) != -1;
	}

	$('.imagecrop-upload').change(function () {
		var $this = $(this);
		var $preview = $(".imagecrop-preview");

		if(!isValidImagePath($this.val())) {
			/* TODO: This probably needs to go through i18n. */
			alert('Please select a valid image!');
			$this.val('');
		}
	});

	$('.imagecrop-preview').Jcrop({onChange: function (coords) {
			var points = coords.x + ',' + coords.y + ',' + coords.x2 + ',' + coords.y2;
			var $points = $('input[name="imagecrop-points"]');
			$points.val(points);
		}
	});
});
