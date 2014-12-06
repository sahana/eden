/**
 * Used by S3ImageCropWidget (modules/s3widgets.py)
 *
 * @ToDo: Doesn't currently work with Inline Component Forms
 */

 $(function () {
    /* Keep this updated with s3.IMAGE_EXTENSIONS */
    var IMAGE_EXTENSIONS = ['png', 'PNG', 'jpg', 'JPG', 'jpeg', 'JPEG'],
        formats = 'png, jpeg or jpg',
        extension,
        $canvas = $('.imagecrop-canvas'),
        canvas = $canvas[0];

    if (undefined == canvas) {
        // Bail
        return;
    }

    var widthLimit = canvas.width;
        heightLimit = canvas.height;
        toScale = true;

    if (widthLimit == 0 || heightLimit == 0) {
        toScale = false;
        // set default Value        
        widthLimit = heightLimit = 600;
    }    

    var isValidImage = function(file) {
        var info = file.type.split('/');
        var filetype = info[0];
		extension = info[info.length - 1];
        if (filetype == 'image') {
            if ($.inArray(extension, IMAGE_EXTENSIONS) != -1) {
                if (extension == 'png' || extension == 'PNG') {
                    extension = 'png';
                }
                else {
                    extension = 'jpeg';
                }
                return true;
            }
        }
    };

    var userEvent,
        scaleFactor;

    var saveEvent = function(e) {
        userEvent = e;        
    };

    var calculateScale = function(canvas_size, image_size) {

        if (image_size[0] > canvas_size[0]) {   
            scaleFactor = canvas_size[0] / image_size[0];
            image_size[0] *= scaleFactor;
            image_size[1] *= scaleFactor;
        }

        if (image_size[1] > canvas_size[1]) {
            scaleFactor = canvas_size[1] / image_size[1];
            image_size[0] *= scaleFactor;
            image_size[1] *= scaleFactor;
        }

        image_size[0] = Math.floor(image_size[0]);
        image_size[1] = Math.floor(image_size[1]);

        return image_size;
    };

    var FileHoverHandler = function(e) {
        e.stopPropagation();
        e.preventDefault();
        e.target.className = 'imagecrop-drag';
        if (e.type == 'dragover') {
            e.target.className = 'imagecrop-drag hover';
        }
    };

    var jCropAPI,   
        scale, 
        fileName,
        image = new Image;

    var loadImage = function(data) {
        var scaled_image;
        // Image uploaded by user
        image.src = data;
        image.onload = function() {
            var canvas_size = [widthLimit, heightLimit];
            var image_size = [image.width, image.height];
            scale = calculateScale(canvas_size, image_size);
            canvas.width = scale[0];
            canvas.height = scale[1];
            canvas.getContext('2d')
                  .drawImage(image, 0, 0, scale[0], scale[1]);
            scaled_image = canvas.toDataURL('image/' + extension);
            if (toScale) {
                $('.imagecrop-data').val(fileName + ';' + scaled_image);
            }
            else {
                // Don't Scale
                $('.imagecrop-data').val(fileName + ';' + data);
            }
            $('#uploaded-image').attr({
                src: scaled_image,
                style: 'display: block'
            });
            $('#select-crop-btn').css({
                display: 'inline'
            });
            $('hr').attr({
                style: 'display:block'
            });
        };
    };

    var $uploadTitle = $('#upload-title'),
        $uploadContainer = $('#upload-container');

    $uploadTitle.bind('click', function(e) {
        $uploadContainer.slideDown('fast', function() {
            $uploadTitle.html(i18n.upload_image);
        });    
    });

    var FileSelectHandler = function(e) {

        if (jCropAPI) {
            jCropAPI.destroy();
        }

        // Hide Upload Div
        setTimeout(function() { 
            $uploadContainer.slideUp('fast', function() {
                $uploadTitle.html('<a>' + i18n.upload_new_image + '</a>');
            });
        }, 500);

        var reader = new FileReader();

        var files = e.target.files || e.originalEvent.dataTransfer.files;
        var file = files[0];
        fileName = file.name;

        saveEvent(e);

        if (e.type == 'drop') {
            // Remove CSS property
            FileHoverHandler(e);
        }

        var $upload = $('.imagecrop-upload');

        if (!isValidImage(file)) {
            alert(i18n.invalid_image + '\n' + i18n.supported_image_formats + ': ' + formats);
            $upload.val('');
            return;
        }

        reader.onload = function(e) {
            loadImage(e.target.result); 
        };

        reader.readAsDataURL(file);
        $upload.val('');
    };

    var $selectCrop = $('#select-crop-btn'),
        $crop = $('#crop-btn'),
        $cancel = $('#remove-btn'),
        $points = $('input[name="imagecrop-points"]');

    var enableCrop = function(e) {
        jCropAPI.enable();
        var b = jCropAPI.getBounds(),
            midx = b[0]/2,
            midy = b[1]/2,
            addx = b[0]/4,
            addy = b[1]/4;

        var defaultSelection = [midx - addx, midy - addy, midx + addx, midy + addy];
        jCropAPI.animateTo(defaultSelection);
        $selectCrop.css({
            display: 'none'
        });
        $crop.css({
            display: 'inline'
        });
        $cancel.css({
            display: 'inline'
        });
    };

    var cropImage = function(e) {

        // Crop the Image
        var $jcropHolder = $('.jcrop-holder');
        var width = parseInt($jcropHolder.css('width').split('px')[0]),
            height = parseInt($jcropHolder.css('height').split('px')[0]);
        var scaleX = image.width / width,
            scaleY = image.height / height;
        var coords = $points.val().split(',');
        var x1 = coords[0],
            y1 = coords[1],
            x2 = coords[2],
            y2 = coords[3];

        // calculate Canvas width
        width = Math.round((x2 - x1) * scaleX);
        // calculate Canvas Height
        height = Math.round((y2 - y1) * scaleY);

        jCropAPI.destroy();
        disableCrop(userEvent);

        $canvas.attr({
            width: width,
            height: height
        });
        canvas.getContext('2d')
              .drawImage(image, Math.round(x1 * scaleX), Math.round(y1 * scaleX), width, height, 0, 0, width, height);
        var data = canvas.toDataURL('image/' + extension);
        loadImage(data);    
    };

    var disableCrop = function(e) {

        jCropAPI.release();
        jCropAPI.disable();

        $crop.css({
            display: 'none'
        });
        $cancel.css({
            display: 'none'
        });
        $selectCrop.css({
            display: 'inline'
        });
    };

    $selectCrop.bind('click', enableCrop);
    $crop.bind('click', cropImage);
    $cancel.bind('click', disableCrop);

    var UpdateCropPoints = function(coords) {
        var points = coords.x + ',' + coords.y + ',' + coords.x2 + ',' + coords.y2;
        $points.val(points); 
    };

    var bounds;

    var EnableCrop = function(e) {
        
        var $this = $(this);

        if (jCropAPI) { 
            jCropAPI.destroy();
            disableCrop(userEvent);
        }

        // $preview.css({ display: 'block' });

        $this.Jcrop({onChange: UpdateCropPoints,
                     opacity: 0.2,
                     bgFade: true,
                     bgColor: 'black',
                     addClass: 'jcrop-light'
                     }, 
                     function() {
                        jCropAPI = this;
                        bounds = jCropAPI.getBounds();
                        jCropAPI.ui.selection.addClass('jcrop-selection');
                        jCropAPI.disable();
                     });
    };

    $('#uploaded-image').bind('load', EnableCrop);

    // Image already stored in DB ( Update form )
    // load the Image

    var imgData = $('.imagecrop-data').attr('value');
    if (typeof imgData != undefined) {
        // dummy Event
        saveEvent(document.createEvent('Event'));
        var img = new Image;
        img.src = imgData;
        img.onload = function(){
            $canvas.attr({
                width: img.width,
                height: img.height
            });
            canvas.getContext('2d')
                  .drawImage(img, 0, 0, img.width, img.height);
            var t = imgData.split('.');
            extension = t[t.length - 1];
            if (extension == 'jpg') {
                extension = 'jpeg';
            }
            fileName = 'upload.' + extension;
            var data = canvas.toDataURL('image/' + extension);
            loadImage(data);
        }
    }

    // Bind Events to catch Image Upload Events
    $('.imagecrop-drag').bind('dragover', FileHoverHandler)
                        .bind('dragleave', FileHoverHandler)
                        .bind('drop', FileSelectHandler);
    $('.imagecrop-upload').bind('change', FileSelectHandler); 

 });
