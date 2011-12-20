function error_color(val, metadata, record, row, col, store)
{
        if(!val)
		val = '';
	var error = val.substring(0,9);
	if( error == '*_error_*')
	{
		//record.set(col,val.substring(9));
		//record.commit();
		return "<font color='red'>" + val.substring(9) + '</font>';
	}
	return val;
}

if(success == 0)
{
	Ext.onReady(function(){
	Ext.Msg.alert('Success!', 'All records were successfully imported ');
	});
}

else
{

	Ext.onReady(function(){
	Ext.Msg.alert('','These records could not be imported. Please edit and import again.');
	var column_model = new Array();
	fields = [];
	var tempmap = map;
	for(i = 0 ;i < map.length; i++)
	{
	    var tempstr = tempmap[i][2].indexOf('--');
		if(tempstr!=-1)
		{
			var check = tempmap[i][2].split(' --> ');
			fields.push( '$k_' + check[0] + ' --> $_' + check[1] + ' --> ' + check[2]);
		}
		
		else
			fields.push(tempmap[i][2]);
	}
	var store = new Ext.data.JsonStore({
		fields : fields,
		root : 'rows'
	});
	var data={};
	number_column = fields.length;
	data['rows'] = invalid_rows;
	store.loadData(data);
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
		temp.renderer = error_color;
		column_model.push(temp);
	}
	column_model.push(action);
	column_model = new Ext.grid.ColumnModel(column_model);
	var re_import_grid = new Ext.grid.EditorGridPanel({
		title : 'Edit invalid rows ',
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
				        
					send.re_import = 'True';	
					send.map = map;
					send.columns = number_column;
					send.resource = resource;
					var time= new Date();
					var modifydate = ''+(time.getUTCFullYear()+'-'+time.getUTCMonth()+'-'+time.getUTCDate()+' '+time.getUTCHours()+':'+time.getUTCMinutes()+':'+time.getUTCSeconds());
					send.modtime = modifydate;
					var posturl = 'http://'+url+'/'+application+'/importer/import_spreadsheet';
					Ext.Ajax.request({
						url : posturl,
						method : 'POST',
						jsonData : send,
						callback : function(options,success,response)
							   {
							        lm.hide();
								window.location = 'http://' + url + '/' + application + '/importer/similar_rows';
						            }	
    		});
					lm.hide();
				}
				}]

		});
	re_import_grid.show();
	//document.write(data);
	});
}
