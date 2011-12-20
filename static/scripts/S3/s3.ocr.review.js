$(document).ready(function() {
    $('form#ocr-review-form a.colorbox').remove();

    $('.ignore-button').filter(':button').click(function() {
	$(this).toggleClass('ignore-button-toggle-yes');
	return false;
    });

    $('.clrbutton').filter(':button').click(function() {
	var buttonid = this.name.split('-')[1];
	try {
	    $('.field-' + buttonid).val('')
	}
	catch(err)
	{
	}

	try {
	    $('.field-' + buttonid).attr('checked', false);
	}
	catch(err)
	{
	}
	return false;
    });

    $('.submit-button').filter(':button').click(function() {
	var ignore_fields = '';
	$.each($('.ignore-button-toggle-yes'), function(index, value) {
	    if (ignore_fields == '')
	    {
		ignore_fields = value.name.split('ignore-')[1];
	    } else {
		ignore_fields += '|'+value.name.split('ignore-')[1];
	    }
	});
	var values = $('#ocr-review-form').serialize();
	$('.error-span').html('')
	//alert(values);
	var dispatch_data = values + '&ignore-fields-list=' + ignore_fields;
	$.ajax({
	    type: 'POST',
	    url: document.location.href,
	    data: dispatch_data,
	    success: function(data) {
		if (data.success) {
		    alert('Data Saved');
		    win_location = window.location.href
		    window.location = win_location.split("upload.pdf")[0]+"upload.pdf"
		} else {
		    var size = 0;
		    for (var key in data.error) {
			$('#'+key+'-error').html(data.error[key]);
			size++;
		    }
		    alert('There are '+size+' Error(s). Resubmit.');
		}
	    },
	    beforeSend: function(jqXHR, settings) {
		$('<div />').addClass('lightbox-bg').appendTo('body').show();
		$('<div />').addClass('modal-loader').html('<img src="/eden/static/img/ajax-loader.gif" /><br/><p>submitting...</p>').appendTo('body');
	    },
	    complete: function(jqXHR, textStatus) {
		$('.lightbox-bg').remove();
		$('.modal-loader').remove();
	    }
	});
	return false;
    });
});
