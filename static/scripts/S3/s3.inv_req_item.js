/**
 * Used by the inv/req controller
 * - supports req_item_quantity_represent
 */

$(document).ready(function() {

   $(document).on('click', '.quantity.ajax_more', function(e) {

		e.preventDefault();

		var DIV = $(this);

		if (DIV.hasClass('collapsed')) {

            var ShipmentType,
                Component;

			if (DIV.hasClass('fulfil')) {
				ShipmentType = 'recv';
                Component = 'track_item';
			} else if (DIV.hasClass('transit')) {
				ShipmentType = 'send';
                Component = 'track_item';
			} else if (DIV.hasClass('commit')) {
				ShipmentType = 'commit';
                Component = 'commit_item';
			}
			DIV.after('<div class="ajax_throbber quantity_req_ajax_throbber"/>')
			   .removeClass('collapsed')
			   .addClass('expanded');

			// Get the req_item_id
			var i,
                re = /req_item\/(\d*).*/i,
                ResultTable,
                LineURL,
                UpdateURL = $('.action-btn', DIV.parent().parent().parent()).attr('href'),
                req_item_id = re.exec(UpdateURL)[1],
                url = S3.Ap.concat('/inv/', ShipmentType, '_item_json.json/', req_item_id);
			$.ajax( {
				url: url,
				dataType: 'json',
				context: DIV
			}).done(function(data) {
                ResultTable = '<table class="recv_table">';
                for (i = 0; i < data.length; i++) {
                    ResultTable += '<tr><td>';
                    if (i === 0) {
                        // Header Row
                        ResultTable += data[0].id;
                    } else {
                        LineURL = S3.Ap.concat('/inv/', ShipmentType, '/',  data[i].id, '/' + Component);
                        ResultTable += "<a href='" + LineURL + "'>" + data[i].name + ' - ' + data[i].date + '</a>';
                    }
                    ResultTable += '</td><td>' + data[i].quantity + '</td></tr>';
                }
                ResultTable += '</table>';
                $('.quantity_req_ajax_throbber', this.parent()).remove();
                this.parent().after(ResultTable);
            });
		} else {
			DIV.removeClass('expanded')
			   .addClass('collapsed');
			$('.recv_table', DIV.parent().parent() ).remove();
		}
	});

});