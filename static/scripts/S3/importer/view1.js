function doJSON(stringData) {
        try {
            var jsonData = Ext.util.JSON.decode(stringData);
            return jsonData;
        }
        catch (err) {
            Ext.MessageBox.alert('ERROR', 'Could not decode ' + stringData);
        }
    }


function view1(importsheet){
   
    Ext.QuickTips.init();	
    Ext.QuickTips.enable();
    var columnlist = new Array(importsheet.columns);
    for(var i=0 ; i< importsheet.columns ; i++)
    { 
            temp = 'column' + i;
//	    temp=eval('('+temp+')');
	    columnlist[i] = temp;
    }
    //columnlist[0]='id';
    //columnlist[0]=eval('('+columnlist[0]+')');
    /*var store=new Ext.data.JsonStore({		
    	 root: 'data',
	 idProperty:'id',
         fields : columnlist,
	 totalProperty : json.rows
    });
   store.loadData(json);*/
   //column model for the grid     
   var columns = (importsheet.columns);
   var column_model = new Array(columns);
   var action = new Ext.ux.grid.RowActions({
			 header: 'Click to delete',
			 autoWidth: false,
			 //keepSelection: true,
			 actions:[{
				 iconCls: 'action-delete',
				 text: 'Delete',
				 tooltip: 'delete',
				 //autoWidth: true,
				 keepSelection: true
			}]
		});
   
   //actions handler for the delete button of each row 
   action.on({
		action:function(grid, record, action, row, col) {
			Ext.Msg.show({
				title: 'Delete?',
			        msg: 'Are you sure you want to delete this row?',
				buttons: Ext.Msg.YESNO,
			        fn: function(btn)
			        	{ 
					if (btn == 'yes'){
						grid.getStore().remove(record);
						}
				 }
				});
		}
   });

   var edit = new Array(importsheet.columns);
   //editor functions for each column 
   for (i=1 ; i< importsheet.columns + 1 ; i++)
   {
       edit[i] = new Ext.form.TextField();
   }
   //makes column model objects
   for ( i=2 ; i< importsheet.columns + 2; i++)
   {
       var obj = {};
       obj.header='Column '+(i-1);
       obj.sortable=true;
       obj.dataIndex=columnlist[i-2];
       obj.editor=edit[i-1];
       column_model[i]=obj;
   }
    var new_row_string = '{';
    var sm2 = new Ext.grid.CheckboxSelectionModel({singleSelect: 'true'});
    column_model[1] = sm2;	//placing the checkboxes before the first column
    column_model[0] = new Ext.grid.RowNumberer();
    //column_model[0] = new Ext.grid.RowNumberer();
    column_model.push(action);
    importsheet.column_model = column_model;
    var sm1 = new Ext.grid.CellSelectionModel();
    //column_model.push(sm1);
    var row_model = Ext.data.Record.create(columnlist);
    //Configuring the grid
    var grid = new Ext.grid.EditorGridPanel({
        title: '<div align="center"><u>Edit</u> \u2794 Select module and resource \u2794 Map columns to fields<p>Edit the spreadsheet, make sure a row with column titles is selected</p></div>',
        renderTo: 'spreadsheet',
        loadMask: true,
        viewConfig:
        {	
       		autoFill: true
        },
        autoFill: true,
        plugins: action,
        height: 380,
        //minColumnWidth: 50,
        store: importsheet.datastore,
        columnLines: true,
        sm: sm2,  
        style : 'text-align:left;', 
        frame : true,
        columns: column_model,
        buttons: [{
                    text: 'Next',
                    handler: function() {
                        importsheet.rows = grid.getStore().getCount();
                        // This function stores the grid
                        /*var gridsave=new Array(grid.getStore().getCount());
                        var i = 0;
				        grid.getStore().each(function(record)						{
                        gridsave[i++] = record.data}
							);
                        //grid.hide();
                        */
                        // From view2.js
                        var selmod = grid.getSelectionModel();
                        if (!selmod.getSelected())
                            Ext.Msg.alert('Error', 'Select column header row');
                        else
                            {	    
                            grid.hide();
                            importsheet.headerobject = selmod.getSelected();
                            view3(importsheet);
                            }
                    }
				}],
        buttonAlign: 'center',
        listeners: {
                afteredit: function(e){
                    // Saves the value in a cell after edit
                    e.record.commit();
                    var temp = e.column;
                    json.data[e.row].temp = e.value;
                } 
        },
        clicksToEdit: 1,
        stripeRows: true,
        tbar: [{
                text: 'Search',
                iconCls: 'action-search',
       	        handler:
		   	     function() {
					Ext.Msg.prompt('Search', 'Enter search text', function(btn, text){
						if (btn == 'ok')
						{
							var k=-1;
							for (i=0; i < importsheet.columns; i++)
							{
								k = importsheet.datastore.find('column'+i, text, 0, true, false);
								if (k != -1)
									break;
							}
							if (k == (-1))
							{
								Ext.Msg.alert('Not found', 'Search string not in spreadsheet ' + k);
							}
							else
							{
								Ext.Msg.alert('Found', 'First matching record is at ' + (k+1));
								sm2.selectRow(k);								
							}
						}
					});
				}
			},'-',
							
			
            {
            text: 'Add row',
            iconCls: 'action-add',
            handler: function() {
                        grid.getStore().insert(0, new row_model);
                        grid.startEditing(0, 0);
                    }
            },
            '-',
            {
            text: 'Remove row',
            iconCls : 'action-delete', 
            handler: function() {
                    try {
                        var selmod = grid.getSelectionModel();
                        if (selmod.hasSelection()){
                            Ext.Msg.show({
                                       title: 'Remove',
                                       buttons: Ext.MessageBox.YESNOCANCEL,
                                       msg: 'Remove ?',
                                       fn: function(btn){
                                               if (btn == 'yes'){
                                                   grid.getStore().remove(grid.getSelectionModel().getSelections());
                                                   
                                                 }
                                           }
                                 });
                            }
                        }
                        catch(err){
                              Ext.Msg.alert('Error', 'Cannot remove row!');
                              }
                    }
            },
            '-'
        ],
	hidden: true
        });
    action.init(grid);
    grid.setAutoScroll(true);
    grid.show();
}

Ext.onReady(function(){
	var columnlist = new Array(json.columns);
   	for(var i=0; i < json.columns ; i++)
    	{ 
       	    temp = 'column' + i;
            //temp = eval('(' + temp + ')');
            columnlist[i]=temp;
        }
    	//columnlist[0]='id';
    	//columnlist[0]=eval('('+columnlist[0]+')');
    	var store=new Ext.data.JsonStore({		
    		root: 'data',
            idProperty:'id',
    		fields : columnlist,
            totalProperty : json.rows
	    });
   	store.loadData(json);
	importsheet.datastore = store;
	importsheet.columns = json.columns;
	view1(importsheet);//.datastore,importsheet.columns);
});
