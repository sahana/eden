function no_similar()
{
	Ext.onReady(function()
	{
		Ext.Msg.alert('', 'No similar rows!!');
	});
}

function similar(similar_rows)
{
	Ext.onReady(function()
	{
		var column_model = new Array();
	fields = [];
	for(i = 0 ;i < map.length; i++)
	{
	    var tempstr = map[i][2].indexOf('--');
		if(tempstr!=-1)
		{
			var check = map[i][2].split(' --> ');
			fields.push( '$k_' + check[0] + ' --> $_' + check[1] + ' --> ' + check[2]);
		}
		else
			fields.push(map[i][2]);
	}
	var store = new Ext.data.ArrayStore({
		fields : fields
	});
	var data = {};
	data['rows'] = similar_rows;
	store.loadData(similar_rows);
	number_column = fields.length;
	/*store.each(function(record)
		{
			console.log(record.get(fields[0]));
		});*/
	var action = new Ext.ux.grid.RowActions({
			 header:'Click to delete',
			 autoWidth: false,
			 //keepSelection: true,
			 actions:[{
				 iconCls: 'action-delete',
				 text: 'Delete',
				 tooltip : 'delete',
				 //autoWidth: true,
				 keepSelection: true
			}]

		});
   //actions handler for the delete button of each row 
   action.on({
		action:function(grid, record, action, row, col) {
			Ext.Msg.show({
				title :'Delete?',
			        msg   : 'Are you sure you want to delete this row?',
				buttons: Ext.Msg.YESNO,
			        fn: function(btn)
			        	{ 
					if(btn=='yes'){
						grid.getStore().remove(record);
						}
				 }
				});
		}
   });
	for( i=0 ; i < number_column ; i++)
	{
		temp = {};
		temp.header = map[i][1];//fields[i];
	        temp.dataIndex = fields[i];
		temp.editor = new Ext.form.TextField();
		//temp.renderer = error_color;
		column_model.push(temp);
	}
	column_model.push(action);
	column_model = new Ext.grid.ColumnModel(column_model);
	var similar_rows_grid = new Ext.grid.EditorGridPanel({
		title : 'Edit similar rows ',
		renderTo: 'spreadsheet',
		columnLines : true,
		width : 'auto',
		plugins : action,
		height : 300,
		viewConfig:{
			forceFit : true
		},
		store : store,
		frame : true,
		colModel : column_model,
		hidden : true,
		buttonAlign : 'center',
		listeners:
			{
				afteredit: function(e){
					e.record.commit();
				}
			},
		buttons :[
			{
				text : 'Import',
				handler: function()
				{
					var lm = new Ext.LoadMask(Ext.getBody(),{msg : 'Importing...'});
					lm.enable();
					lm.show();
					var send = {};
					send.spreadsheet = new Array();
					send.rows = 0;
					store.each(function()
					{
						var temp = new Array();
						var i = 0;
						while(i < number_column)
						{
							temp.push(this.get((fields[i])));
							i++;
						}

						send.spreadsheet.push(temp);
						send.rows += 1;
					});
				        
					send.similar_rows = 'True';	
					send.map = map;
					send.columns = number_column;
					send.resource = resource;
					var time= new Date();
					var modifydate = ''+(time.getUTCFullYear()+'-'+time.getUTCMonth()+'-'+time.getUTCDate()+' '+time.getUTCHours()+':'+time.getUTCMinutes()+':'+time.getUTCSeconds());
					send.modtime = modifydate;
					var posturl = 'http://' + url + '/' + application + '/importer/import_spreadsheet';
					Ext.Ajax.request({
						url : posturl,
						method : 'POST',
						jsonData : send,
						callback : function(options,success,response)
							   {
							        lm.hide();
								window.location = 'http://' + url + '/' + application + '/importer/re_import';
						            }	
    		});
					//console.log(send);
					lm.hide();
				}
				}]

		});
	similar_rows_grid.show();

	});
}

