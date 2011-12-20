function import_spreadsheet(importsheet,lm)
{
	var temp=importsheet.table.split('_');
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
		for(var j=0;j<importsheet.columns;j++)
		{
			var field="\""+importsheet.map[j][2]+"\"";
			Ext.Msg.alert('',field);
			if(field!=''){
				if(importsheet.map[j][2].substring(0,3)=='opt')
				{
					rowobj+=field+':';
					rowobj+="{\"@value\":\"1\"";
					rowobj+=",\"$\":\""+importsheet.data[i][j]+"\"}";
				}
				else
					rowobj+=field+":\""+importsheet.data[i][j]+"\"";
				if(j!=importsheet.columns-1) 
					rowobj+=',';
			}
			
		}
		rowobj+=",\"@modified_on\":\"";
		rowobj+=modifydate;
		rowobj+="\"}";
		try{
			rowobj=eval('('+rowobj+')');
		}
		catch(err)
		{
		}
		jsonss.push(rowobj);
	}
	var posturl='http://{{=request.env.http_host}}/{{=request.application}}/'+prefix+'/'+name+'/create.json?p_l='+jsonss.length;
	var sendobj="{\""+str+"\":"+jsonss+"}";
	var send="{\""+str+"\":\"\"}";
 	send=eval('('+send+')');
	send[str]=jsonss;
	//send[str]=new Array();
	//send[str].push(rowobj);
	Ext.Ajax.request({
		url : posturl,
		jsonData: send,//send as body,
		method : 'POST',
		success : function(r,o)
			{
				lm.hide();
				Ext.Msg.alert('Success','Import successful!');
				//document.write('Successfully sent '+r.status);
			},
		failure: function(r,o)
			{
				lm.hide();
				Ext.Msg.alert('Failure','Import Failed');

			//				document.write('Sending failed<br/> '+r.status+'<br/>'+r.tree);
			}
	});
}
