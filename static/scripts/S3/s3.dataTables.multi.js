/* Support for a page with multiple dataTables such as DRRPP's 'Organisations' page */
S3.pluginDefaults = {
	'dataTables': {
		'dom': 'fril<"dataTable_table"t>pi',
		'lengthMenu': [[ 25, 50, -1], [ 25, 50, i18n.all]],
		'order': [[1, 'asc']],
		'pageLength': 25,
		'pagingType': 'full_numbers',
        'processing': true,
		'searching': true,
		'serverSide': false,
		'rowCallback': function(nRow, aData, iDisplayIndex) {
			var instance_id = this.data('instance');
			var instance = S3.dataTablesInstances[instance_id];
			var $row = $(nRow);

			if (instance.bulk_actions) {
				var row_id = parseInt(aData[0]);
				chbx = $('<input/>').attr({'value': row_id,
				                           'name': 'action_selected',
				                           'type': 'checkbox'});
				$row.children().first().html(chbx);
			}

			if (instance.row_actions) {
				var row_id = parseInt(aData[0]);

				$row.children().last().html('');

				for (var i=0; i < instance.row_actions.length; i++) {
					var action = instance.row_actions[i];

					if (action.restrict.indexOf(row_id) != -1) {
						btn = $('<a/>').attr({'href': action.url.replace('%5Bid%5D', row_id)})
									   .text(action.label)
									   .addClass('.btn')
									   .addClass(action.css);
						$row.children().last().append(btn);
					}
				}
			}
		}
	}
};

$(document).ready(function() {
	$('table.dataTable').each(function(index) {
		var table = $(this);
		var options = $.extend(
			{},
			S3.pluginDefaults.dataTables,
			S3.dataTablesInstances[index].options
		);
		table.data('instance', index).dataTable(options);
	});

	$("form.dataTable-actions select[name='action']").each(function(index) {
		$(this).closest('form').attr('action', this.value);
	}).on('change', function() {
		$(this).closest('form').attr('action', this.value);
	});
});
