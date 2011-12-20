// Create a standard HttpProxy instance.
var proxy = new Ext.data.HttpProxy({
    // Records are loaded via the JSON representation of the resource
    url: '{{=URL(vars={'format':'json'})}}'
});

{{table = request.controller + '_' + request.function}}

// JsonReader.  Notice additional meta-data params for defining the core attributes of your json-response
var reader = new Ext.data.JsonReader({
    totalProperty: '@results',
    successProperty: 'success',
    idProperty: '@uuid',
    root: '$_{{=table}}',       // We only want the data for our table
    messageProperty: 'message'  // <-- New "messageProperty" meta-data
}, [
    {{for field in form.fields:}}
      {{if form.custom.widget[field]:}}
        {
            name: '{{=form.custom.widget[field].attributes['_name']}}',
        {{requires = form.custom.widget[field].attributes['requires']}}
          {{if not isinstance(requires, (list, tuple)):}}
            {{requires = [requires]}}
          {{pass}}
          {{for require in requires:}}
            {{if 'IS_NOT_EMPTY' in str(require):}}
              allowBlank: false
            {{pass}}
          {{pass}}
        },
      {{pass}}
    {{pass}}
]);

// Store collects the Proxy and Reader together.
var store = new Ext.data.Store({
    root: '$_{{=table}}',    // We only want the data for our table
    //id: 'user',
    restful: true,
    proxy: proxy,
    reader: reader,
    paramNames: {
        start : 'start',
        limit : 'limit',
        sort : 'sort',
        dir : 'dir'
    }
});
    
// Load the store immediately (for remote Store)
// Server-side paging enabled.
store.load({params:{start:0, limit:{{=pagesize}}}});

// Get list of columns from the 'form' var
var userColumns =  [
    //{header: "ID", width: 40, sortable: true, dataIndex: 'id'},
  {{for field in form.fields:}}
    {{if form.custom.widget[field]:}}
        {{if form.custom.widget[field].attributes['_name'] != 'Id':}}
            {header: "{{=form.custom.label[field]}}", sortable: true, dataIndex: '{{=form.custom.widget[field].attributes['_name']}}'},
        {{pass}}
    {{pass}}
  {{pass}}
];


// Shortcut to avoid multiple lookups
var xg = Ext.grid;
var sm = new xg.CheckboxSelectionModel();

// Create a typical GridPanel
var userGrid = new xg.GridPanel({
    renderTo: 'table-container',
    iconCls: 'icon-grid',
    frame: true,
    autoScroll: true,
    columns: userColumns,
    //cm: new xg.ColumnModel({
    //        defaults: {
    //            width: 100,
    //            sortable: true
    //        },
    //        columns: [
    //            sm,
    //            userColumns
    //        ]
    //    }),
    sm: sm,
    columnLines: true,
    height: 300,
    //autoHeight: true, // autoHeight means no scrollbars
    store: store,
    // Paging bar on the bottom
    bbar: new Ext.PagingToolbar({
        pageSize: {{=pagesize}},
        store: store,
        pageSize: {{=pagesize}},
        displayInfo: true,
        displayMsg: '{{=T('Displaying records')}} {0} - {1} {{=T('of')}} {2}',
        emptyMsg: "{{=s3.crud_strings[table].msg_list_empty}}",
        beforePageText : '{{=T('Page')}}',
        //items: [
        //    '-', {
        //    pressed: true,
        //    enableToggle:true,
        //    text: '{{=T('Show Preview')}}',
        //    cls: 'x-btn-text-icon details',
        //    toggleHandler: function(btn, pressed){
        //        var view = userGrid.getView();
        //        view.showPreview = pressed;
        //        view.refresh();
        //    }
        //}]
    }),
    //viewConfig: {
        // This should be false to allow a horizontal scrollbar
    //    forceFit: true
    //}
});
