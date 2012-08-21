S3.pluginDefaults = {
	"dataTables": {
		"iDisplayLength": 25,
		"bProcessing": true,
		"bServerSide": false,
		"bFilter": true,
		"aaSorting": [[1, 'asc']],
		"sDom": 'fril<"dataTable_table"t>pi',
		"sPaginationType": 'full_numbers',
        "aLengthMenu": [[ 25, 50, -1], [ 25, 50, S3.i18n.all]],
		"fnRowCallback": function(nRow, aData, iDisplayIndex) {
			var instance_id = this.data("instance");
			var instance = S3.dataTablesInstances[instance_id];
			var $row = $(nRow);

			if (instance.bulk_actions) {
				var row_id = parseInt(aData[0]);
				chbx = $('<input/>').attr({"value": row_id,
				                           "name": "action_selected",
				                           "type": "checkbox"});
				$row.children().first().html(chbx);
			}

			if (instance.row_actions) {
				var row_id = parseInt(aData[0]);

				$row.children().last().html("");

				for (var i=0; i < instance.row_actions.length; i++) {
					var action = instance.row_actions[i];

					if (action.restrict.indexOf(row_id) != -1) {
						btn = $('<a/>').attr({"href": action.url.replace("%5Bid%5D", row_id)})
									   .text(action.label)
									   .addClass(".btn")
									   .addClass(action.css);
						$row.children().last().append(btn);
					}
				}
			}

			// temp
			//$row.children(":eq(1)").wrapInner('<a href="' + row_id + '"/>');
		}
	}
};

$(document).ready(function() {
	$("table.dataTable").each(function(index) {
		var table = $(this);
		var options = $.extend(
			{},
			S3.pluginDefaults.dataTables,
			S3.dataTablesInstances[index].options
		);
		table.data("instance", index).dataTable(options);
	});

	$("form.dataTable-actions select[name='action']").each(function(index) {
		$(this).closest('form').attr('action', this.value);
	}).on('change', function() {
		$(this).closest('form').attr('action', this.value);
	});
});
