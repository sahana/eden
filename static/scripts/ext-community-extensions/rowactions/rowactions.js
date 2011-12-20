// vim: ts=4:sw=4:nu:fdc=4:nospell
/**
 * Ext.ux.grid.RowActions Plugin Example Application
 *
 * @author    Ing. Jozef Sakáloš
 * @date      22. March 2008
 * @version   $Id: rowactions.js 138 2009-03-20 21:22:35Z jozo $
 *
 * @license rowactions.js is licensed under the terms of
 * the Open Source LGPL 3.0 license.  Commercial use is permitted to the extent
 * that the code/component(s) do NOT become part of another Open Source or Commercially
 * licensed development library or toolkit without explicit permission.
 * 
 * License details: http://www.gnu.org/licenses/lgpl.html
 */

/*global Ext, WebPage, Example, console, window */

Ext.BLANK_IMAGE_URL = '../ext/resources/images/default/s.gif';
Ext.ns('Example');
Example.version = '1.0';

// create pre-configured grid class
Example.Grid = Ext.extend(Ext.grid.GridPanel, {

	// {{{
	 initComponent:function() {

	 	// Create row expander
		this.expander = new Ext.grid.RowExpander({
			tpl: new Ext.Template(
				 '<p style="margin:0 0 4px 8px"><b>Company:</b> {company}</p>'
				,'<p style="margin:0 0 4px 8px"><b>Summary:</b> {desc}</p>'
			)
		});

	 	// Create RowActions Plugin
	 	this.action = new Ext.ux.grid.RowActions({
			 header:'Actions'
//			,autoWidth:false
//			,hideMode:'display'
			,keepSelection:true
			,actions:[{
				 iconIndex:'action1'
				,qtipIndex:'qtip1'
				,iconCls:'icon-open'
				,tooltip:'Open'
			},{
				 iconCls:'icon-wrench'
				,tooltip:'Configure'
				,qtipIndex:'qtip2'
				,iconIndex:'action2'
				,hideIndex:'hide2'
//				,text:'Open'
			},{
				 iconIndex:'action3'
				,qtipIndex:'qtip3'
				,iconCls:'icon-user'
				,tooltip:'User'
				,style:'background-color:yellow'
			}]
			,groupActions:[{
				 iconCls:'icon-del-table'
				,qtip:'Remove Table'
			},{
				 iconCls:'icon-add-table'
				,qtip:'Add Table - with callback'
				,callback:function(grid, records, action, groupId) {
					Ext.ux.Toast.msg('Callback: icon-add-table', 'Group: <b>{0}</b>, action: <b>{1}</b>, records: <b>{2}</b>', groupId, action, records.length);
				}
			},{
				 iconCls:'icon-graph'
				,qtip:'View Graph'
				,align:'left'
			}]
			,callbacks:{
				'icon-plus':function(grid, record, action, row, col) {
					Ext.ux.Toast.msg('Callback: icon-plus', 'You have clicked row: <b>{0}</b>, action: <b>{0}</b>', row, action);
				}
			}
		});

		// dummy action event handler - just outputs some arguments to console
		this.action.on({
			action:function(grid, record, action, row, col) {
				Ext.ux.Toast.msg('Event: action', 'You have clicked row: <b>{0}</b>, action: <b>{1}</b>', row, action);
			}
			,beforeaction:function() {
				Ext.ux.Toast.msg('Event: beforeaction', 'You can cancel the action by returning false from this event handler.');
			}
			,beforegroupaction:function() {
				Ext.ux.Toast.msg('Event: beforegroupaction', 'You can cancel the action by returning false from this event handler.');
			}
			,groupaction:function(grid, records, action, groupId) {
				Ext.ux.Toast.msg('Event: groupaction', 'Group: <b>{0}</b>, action: <b>{1}</b>, records: <b>{2}</b>', groupId, action, records.length);
			}
		});

		// configure the grid
		Ext.apply(this, {
			 store:new Ext.data.GroupingStore({
				reader:new Ext.data.JsonReader({
					 id:'company'
					,totalProperty:'totalCount'
					,root:'rows'
					,fields:[
						{name: 'company'}
					   ,{name: 'lastChange', type: 'date', dateFormat: 'n/j h:ia'}
					   ,{name: 'industry'}
					   ,{name: 'desc'}
					   ,{name: 'action1', type: 'string'}
					   ,{name: 'action2', type: 'string'}
					   ,{name: 'action3', type: 'string'}
					   ,{name: 'qtip1', type: 'string'}
					   ,{name: 'qtip2', type: 'string'}
					   ,{name: 'qtip3', type: 'string'}
					   ,{name: 'hide2', type: 'boolean'}
					]
				})
				,proxy:new Ext.data.HttpProxy({url:'get-grid-data.php'})
				,groupField:'industry'
				,sortInfo:{field:'company', direction:'ASC'}
				,listeners:{
					load:{scope:this, fn:function() {
						this.getSelectionModel().selectFirstRow();
					}}
				}
			})
			,columns:[
				 this.expander
				,{id:'company',header: "Company", width: 40, sortable: true, dataIndex: 'company'}
				,{header: "Industry", width: 20, sortable: true, dataIndex: 'industry'}
				,{header: "Last Updated", width: 20, sortable: true, renderer: Ext.util.Format.dateRenderer('m/d/Y'), dataIndex: 'lastChange'}
				,this.action
			]
			,plugins:[this.action, this.expander]
			,view: new Ext.grid.GroupingView({
				 forceFit:true
				,groupTextTpl:'{text} ({[values.rs.length]} {[values.rs.length > 1 ? "Items" : "Item"]})'
			})
			,loadMask:true
//			,viewConfig:{forceFit:true}
		}); // eo apply

		// add paging toolbar
		this.bbar = new Ext.PagingToolbar({
			 store:this.store
			,displayInfo:true
			,pageSize:10
		});

		// call parent
		Example.Grid.superclass.initComponent.apply(this, arguments);
	} // eo function initComponent
	// }}}
	// {{{
	,onRender:function() {

		// call parent
		Example.Grid.superclass.onRender.apply(this, arguments);

		// start w/o grouping
//		this.store.clearGrouping();

		// load the store
		this.store.load({params:{start:0, limit:10}});

	} // eo function onRender
	// }}}

}); // eo extend

// register component
Ext.reg('examplegrid', Example.Grid);

// application entry point
Ext.onReady(function() {
    Ext.QuickTips.init();

	var adsenseHost = 
		   'rowactions.localhost' === window.location.host
		|| 'rowactions.extjs.eu' === window.location.host
	;
	var page = new WebPage({
		 version:Example.version
		,westContent:'west-content'
		,centerContent:'center-content'
		,adRowContent:adsenseHost ? 'adrow-content' : undefined
	});

	var ads = Ext.getBody().select('div.adsense');
	if(adsenseHost) {
		ads.removeClass('x-hidden');
	}
	else {
		ads.remove();
	}

	// window with grid
    var win = new Ext.Window({
         width:600
		,minWidth:320
        ,id:'agwin'
        ,height:400
        ,layout:'fit'
        ,border:false
		,plain:true
        ,closable:false
        ,title:Ext.get('page-title').dom.innerHTML
		,items:{xtype:'examplegrid',id:'actiongrid'}
    });
    win.show();
});

// eof
