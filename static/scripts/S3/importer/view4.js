function cmparr(arr1, arr2)
{
	if(arr1.length != arr2.length)
	{
		return false;
	}
	var check=0;
	for(i=0;i<arr1.length;i++)
		if(arr1[i] === arr2[i])
			check++;
	if(check == arr1.length)
		return true;
	else
		return false;
}

function alertmessage4()
{
	$(document).ready(function()
	{
		$('#message3').hide();
		$('#message4').addClass('confirmation');
		$('#message4').show('slow');
	});
}

function view4(importsheet)
{
    var num_resources = importsheet.final_resources.length;
    var store = importsheet.fields;
    Ext.QuickTips.init();
    var i=0;
    var colnames=new Array(importsheet.columns);
    while(i<importsheet.columns)
    {
	    colnames[i]=importsheet.headerobject.get('column'+i);
	    i++;
    }
    i=0;
    var resource_combo=new Array(importsheet.columns);
    while(i < importsheet.columns)
    {
	    resource_combo[i] = {};
	    resource_combo[i].fieldLabel = colnames[i];
	    resource_combo[i].name=colnames[i]+'_resource';
	    resource_combo[i].id=colnames[i]+'_resource';
	    resource_combo[i].store=importsheet.fields;
	    resource_combo[i].allowBlank=false;
	    resource_combo[i].blankText='You must select a resource';
	    resource_combo[i].emptyText='Select a resource';
	    resource_combo[i].editable=false;
	    resource_combo[i].triggerAction='all';
	    resource_combo[i].width = 400;
	    resource_combo[i].typeAhead=true;
	    resource_combo[i]= new Ext.form.ComboBox(resource_combo[i]);
	    i++;
    }
    var modules = new Ext.form.FieldSet({
		items : resource_combo,
		labelWidth : 350,
		autoHeight : true,
		width :650 });
    var container = { xtype : 'container',
	    	      layout : 'hbox',
		      height : 600,
		      layoutConfig :{
				align : 'stretch'
				},
			items : [modules]//,fields]
    		    };
	var columnmap=new Ext.form.FormPanel({
	title: 'Edit spreadsheet \u2794 Select table \u2794 <u>Map columns to fields</u><br/>Select which columns go to which table fields',
        renderTo: 'spreadsheet',
        frame: true,
	autoScroll : true,
	labelAlign: 'left',
        height : 500,
	items: resource_combo,
	//items : container,
	buttons:[
		{
			text: 'Back',
			handler:
				function(){
						columnmap.hide();
						columnmap.destroy();
						view3(importsheet);
					}
		},
		{	text: 'Import',
			handler: function(){
					importsheet.rows=importsheet.datastore.getCount();
					importsheet.data=new Array();
					//Function which converts the spreadsheet to a list of lists, make a separate function
					importsheet.datastore.each(function()
					{
				
						var i=0;
						var temp=new Array();
						while(i<importsheet.columns)
						{
							temp.push(this.get(('column'+i)));
							i++;
						}
						importsheet.data.push(temp);
					});
 					//extract column headers from the header row object
					var i=0;
					map_from_ss_to_field=[];
					var send = {};
					send.json = {}
					while(i < importsheet.columns)
					{
						if(resource_combo[i].getValue()=='')
						{
							Ext.Msg.alert('Error','Map all columns');
							break;
						}
						map_from_ss_to_field.push([i,resource_combo[i].getName().replace('_resource',''),resource_combo[i].getValue()]);
						i++;
					}
				        importsheet.resource = importsheet.final_resources;	
					importsheet.map=map_from_ss_to_field;
					var headrow=new Array();
					i=0;
					while(i < importsheet.columns)
					{
						headrow.push(importsheet.headerobject.get('column'+i));
						i++;
					}
					importsheet.header_row_labels=headrow;
					i=0;
					var header_row=0;
					//find location of header row
					while(i < importsheet.rows){
 						if(cmparr(importsheet.data[i],importsheet.header_row_labels))
						{
							header_row=i;
							importsheet.header_row_index=i;
							break;
						}	
						i++;	
					}
					 var lm = new Ext.LoadMask(Ext.get('spreadsheet'),{msg : 'Importing...'});
				     	 lm.enable();	     
					 lm.show();
				 	 send.spreadsheet = importsheet.data;
					 send.resource = importsheet.final_resources;
					 send.map = importsheet.map;
					 send.header_row = importsheet.header_row_index;
					 send.rows=importsheet.rows;
					 send.columns=importsheet.columns;
					 var time=new Date();
				         var modifydate=''+(time.getUTCFullYear()+'-'+time.getUTCMonth()+'-'+time.getUTCDate()+' '+time.getUTCHours()+':'+time.getUTCMinutes()+':'+time.getUTCSeconds());
	
					 send.modtime=modifydate;
					 var posturl = 'http://'+url+'/'+application+'/importer/import_spreadsheet';
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
		}}],
       buttonAlign: 'center',
       autoShow : true
	});
	
	columnmap.show(); 

}










				 //Import function
					      	/*var temp=importsheet.table.split('_');
						var prefix=temp[0];
						var name=temp[1];
						var str='$_';
						str+=prefix+'_'+name;
						var jsonss=new Array(); //the array which will have json objects of each row
						time=new Date();
						var modifydate=''+(time.getUTCFullYear()+'-'+time.getUTCMonth()+'-'+time.getUTCDate()+' '+time.getUTCHours()+':'+time.getUTCMinutes()+':'+time.getUTCSeconds());
	//making importable json object of the spreadsheet data
						for(var i=0;i<importsheet.rows;i++)
						{
							if(i==importsheet.header_row_index)
								continue;
							var rowobj='{';
						//	var rowobj={};
							for(var j=0;j<importsheet.columns;j++)
							{
								
								var field="\""+importsheet.map[j][2]+"\"";
								//Ext.Msg.alert("",field);
								if(field!=''){
								if(importsheet.map[j][2].substring(0,4)=="\"opt")
								{
									console.log(importsheet.map[j][2],"_");
									rowobj+=field+":";
									//rowobj[field]["@value"]=
									rowobj+="{\"@value\":\"1\"";
									rowobj+=",\"$\":\""+importsheet.data[i][j]+"\"}";
								}
								else
									rowobj+=field+":\""+importsheet.data[i][j]+"\"";
								if(j!=importsheet.columns-1) 
									rowobj+=",";
								}
										
			
							}
							rowobj+=",\"@modified_on\":\"";
							rowobj+=modifydate;
							rowobj+="\"}";
							jsonss.push(rowobj);
						}
						//document.write(jsonss);
						/*
						var posturl="http://"+url+"/"+application+"/"+prefix+"/"+name+"/create.json?p_l="+jsonss.length;
						//var send="{\""+str+"\":\"\"}";
						var send={};
					 	//send=eval('('+send+')');
						send[str]=jsonss;
						Ext.Ajax.request({
							scope: this,
							url : posturl,
							jsonData: send,//send as body,
							method : 'POST',
							success : function(r,o)
							{
								lm.hide();
								Ext.Msg.alert("Success","Import successful!");
							},
							failure: function(r,o)
							{
								lm.hide();
								importsheet.error_rows=new Array();
							 	try{
									var re_import = eval('('+r.responseText+')');
									re_import=re_import.tree
									var i=0;
									var j=0;
									var jlim=importsheet.datastore.getCount();
									importsheet.incorrect_rows=[];
									importsheet.correct_rows=[];
									while(j < jlim-1 )
									{
										if( j == importsheet.header_row_index)
											continue;
										i=0;
										while(i < importsheet.columns)
										{
											if(re_import[str][j][importsheet.map[i][2]].hasOwnProperty('@error'))
											{
												console.log("Error detected in row ",j+1,re_import[str][j]);
												importsheet.incorrect_rows.push(j);
												break;																				}
											i++;
										}
										j++;
									}
									//console.log("The erroneous records are ",importsheet.error_rows);
									//console.log("and the incorrect rows are ",importsheet.incorrect_rows);
									var num_errors=importsheet.incorrect_rows.length;
									var i=0;
									while(i < importsheet.incorrect_rows.length)
									{
										rowloc = importsheet.incorrect_rows[i];
										importsheet.incorrect_rows[i]=re_import[importsheet.incorrect_rows[i]];
										i++;
									}
									console.log(importsheet.incorrect_rows);
								}
								catch(err)
								{
									Ext.Msg.alert("","Error processing returned tree in row "+j+" column"+i);
									console.log("The erroneous records are ",importsheet.error_rows);
								}
								var field='\"'+importsheet.map[j][2]+'\"';
								while(i < importsheet.rows)
								{
									var record = re_import["tree"][str];
									document.write(record+'<br/>');
									i++;
								}
						
					*/
								/*			
								Ext.Msg.show({
										title : "Import failed",
										msg   : "Some records could not be imported. Would you like to edit the records which could not be imported?",
										buttons: Ext.Msg.YESNO,
										fn : function(btn)
											{
												if(btn=="no")
													return;
												else
												//call post import function
												{}
											}
										});
							}
							});
							}.defer(50,this));*/
	
    /*
    	//build the sheet to be imported as 2d array
        var row=0;
	grid_data.each(function(){
			row++;
		});
	var importsheet={}
	importsheet.rows=row;
	importsheet.columns=numcol;
	importsheet.data=new Array();
	grid_data.each(function()
			{
			
				var i=0;
				var temp=new Array();
				while(i<numcol)
				{
					temp.push(this.get(('column'+i)));
					i++;
				}
				importsheet.data.push(temp);
			});
	Ext.Ajax.request({
			url :'recvdata',
			method: 'POST',
			success: function()
				{
					Ext.Msg.alert("","SUCCESS!!");
					},
			failure: function(){Ext.Msg.alert("","FAILURE!!");},
			scope: this,
			params : {
					spreadsheet : importsheet.data,
					col : numcol,
					row : row
					}
	});

	//extract column headers from the header row object
	var i=0;
	var headrow=new Array();
	while(i<numcol)
	{
		headrow.push(header.get('column'+i));
		i++;
	}
	i=0;
	var header_row=0;
	//find location of header row
	while(i<row){
 		if(cmparr(importsheet.data[i],headrow))
		{
			header_row=i;
			break;
		}
	}
}*/
