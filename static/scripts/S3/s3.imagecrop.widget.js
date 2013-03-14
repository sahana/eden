$(function () {
	/* NOTE: Keep this in sync with s3.IMAGE_EXTENSIONS from 00_settings.py */
	var IMAGE_EXTENSIONS = ['png', 'PNG', 'jpg', 'JPG', 'jpeg', 'JPEG', 'gif', 'GIF', 'tif', 'TIF', 'tiff', 'TIFF', 'bmp', 'BMP', 'raw', 'RAW'];

	var isValidImagePathfunction = function(path) {
		var extension = path.split('.');
		extension = extension[extension.length - 1];

		return $.inArray(extension, IMAGE_EXTENSIONS) != -1;
	}

	var calculateScale = function(canvas_size, image_size) {
		var scale;
		if (image_size[0] > canvas_size[0]) {
			scale = canvas_size[0] / image_size[0];
			image_size[0] *= scale;
			image_size[1] *= scale;
		}

		if (image_size[1] > canvas_size[1]) {
			scale = canvas_size[1] / image_size[1];
			image_size[0] *= scale;
			image_size[1] *= scale;
		}

		image_size[0] = Math.floor(image_size[0]);
		image_size[1] = Math.floor(image_size[1]);

		s3_debug(image_size);
		return image_size;
	}

	var jCropAPI;

	$('.imagecrop-upload').change(function() {
		var $this = $(this);
		var $preview = $('.imagecrop-preview');

		if(!isValidImagePath($this.val())) {
			alert(i18n.invalid_image);
			$this.val('');
		}
	});

	$('.imagecrop-preview').Jcrop({
        onChange: function(coords) {
			var points = coords.x + ',' + coords.y + ',' + coords.x2 + ',' + coords.y2;
			var $points = $('input[name="imagecrop-points"]');
			$points.val(points);
		}
	}, function () {
		jCropAPI = this;
		this.disable();
	});

	$('.imagecrop-toggle').click(function() {
        if ($(this).val() === i18n.crop_image) {
            $(this).val(i18n.cancel_crop);
            $('.imagecrop-help').show();
            jCropAPI.enable();
        } else {
            $(this).val(i18n.crop_image);
            $('.imagecrop-help').hide();
            jCropAPI.release();
            jCropAPI.disable();
            $('input[name="imagecrop-points"]').val('');
        }
	});

	$('.imagecrop-canvas').bind('dragover', function(e) {e.preventDefault();});
	$('.imagecrop-canvas').bind('drop', function(e) {
		e.preventDefault();
		var reader = new FileReader();
		var $this = $(this);
		var fileName = e.originalEvent.dataTransfer.files[0].name;
		reader.onload = function(e) {
			var image = new Image();
			image.src = e.target.result;
			s3_debug(e.target);
			image.onload = function() {
				var scale = calculateScale([$this.width(), $this.height()],
                                           [this.width, this.height]);
				$this[0].width = scale[0];
				$this[0].height = scale[1];
				$this[0].getContext('2d')
                        .drawImage(this, 0, 0, scale[0], scale[1]);
				$('.imagecrop-upload').hide();
				$('.imagecrop-data').val(fileName + ';' + $this[0].toDataURL());
				$this.Jcrop({onChange: function (coords) {
						var points = coords.x + ',' + coords.y + ',' + coords.x2 + ',' + coords.y2;
						var $points = $('input[name="imagecrop-points"]');
						$points.val(points);
					}
				}, function() {
					jCropAPI = this;
				});
			};
		};
		reader.readAsDataURL(e.originalEvent.dataTransfer.files[0]);
	});
});
