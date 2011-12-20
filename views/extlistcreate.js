// Application instance for showing user-feedback messages.
var App = new Ext.App({});

// Create a standard HttpProxy instance.
var proxy = new Ext.data.HttpProxy({
    // Records are loaded via the JSON representation of the resource
    url: '{{=URL(vars={'format':'json'})}}'
});


var editor = new Ext.ux.grid.RowEditor({
    saveText: '{{=T('Update')}}',
    cancelText: '{{=T('Cancel')}}',
    commitChangesText: '{{=T('You need to commit or cancel your changes')}}',
    errorText: '{{=T('Errors')}}'
});
    
{{table = request.controller + '_' + request.function}}

// JsonReader.  Notice additional meta-data params for defining the core attributes of your json-response
var reader = new Ext.data.JsonReader({
    totalProperty: '@results',
    successProperty: 'success',
    //idProperty: '@uuid',      // We don't support URLs of the format: resource/uuid
    root: '$_{{=table}}',       // We only want the data for our table
    messageProperty: 'message'  // <-- New "messageProperty" meta-data
}, [
        {
            name: '@uuid',
            allowBlank: false
        },
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

// The new DataWriter component.
var writer = new Ext.data.JsonWriter({
    encode: false   // <-- don't return encoded JSON -- causes Ext.Ajax#request to send data using jsonData config rather than HTTP params
});

// Store collects the Proxy, Reader and Writer together.
var store = new Ext.data.Store({
    totalProperty: '@results',
    successProperty: 'success',
    //idProperty: '@uuid',
    root: '$_{{=table}}',    // We only want the data for our table
    //id: 'user',
    restful: true,
    proxy: proxy,
    reader: reader,
    writer: writer,
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

////
// ***New*** centralized listening of DataProxy events "beforewrite", "write" and "writeexception"
// upon Ext.data.DataProxy class.  This is handy for centralizing user-feedback messaging into one place rather than
// attaching listeners to EACH Store.
//
// Listen to all DataProxy beforewrite events
//
Ext.data.DataProxy.addListener('beforewrite', function(proxy, action) {
    App.setAlert(App.STATUS_NOTICE, "Before " + action);
});

////
// all write events
//
Ext.data.DataProxy.addListener('write', function(proxy, action, result, res, rs) {
    App.setAlert(true, action + ':' + res.message);
});

////
// all exception events
//
Ext.data.DataProxy.addListener('exception', function(proxy, type, action, options, res) {
    App.setAlert(false, "Something bad happened while executing " + action);
});

// Get list of columns from the 'form' var
var userColumns =  [
    //{header: "ID", width: 40, sortable: true, dataIndex: 'id'},
  {{for field in form.fields:}}
    {{if form.custom.widget[field]:}}
        {{if form.custom.widget[field].attributes['_name'] != 'Id':}}
            {
                header: "{{=form.custom.label[field]}}",
                sortable: true,
                dataIndex: '{{=form.custom.widget[field].attributes['_name']}}',
            {{requires = form.custom.widget[field].attributes['requires']}}
            {{if not isinstance(requires, (list, tuple)):}}
              {{requires = [requires]}}
            {{pass}}
            {{is_date = 0}}
            {{for require in requires:}}
              {{if 'IS_DATE' in str(require):}}
                {{is_date = 1}}
              {{pass}}
            {{pass}}
            {{if is_date == 1:}}
                editor: new Ext.form.DateField({})
            {{else:}}
                editor: new Ext.form.TextField({})
            {{pass}}
            },
        {{pass}}
    {{pass}}
  {{pass}}
];


// Shortcut to avoid multiple lookups
var xg = Ext.grid;
var sm = new xg.CheckboxSelectionModel();

// Create a typical GridPanel with RowEditor plugin
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
    plugins: [editor],
    // Top toolbar for Add/Delete options (ToDo: Add Edit)
    tbar: [{
        text: '{{=T('Add')}}',
        iconCls: 'silk-add',
        handler: onAdd
    }, '-', {
        text: '{{=T('Delete')}}',
        iconCls: 'silk-delete',
        handler: onDelete
    }, '-'],
    // Paging bar on the bottom
    bbar: new Ext.PagingToolbar({
        pageSize: {{=pagesize}},
        store: store,
        displayInfo: true,
        displayMsg: '{{=T('Displaying records')}} {0} - {1} {{=T('of')}} {2}',
        emptyMsg: "{{=s3.crud_strings[table].msg_list_empty}}",
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

/**
 * onAdd
 */
function onAdd(btn, ev) {
    var u = new userGrid.store.recordType({
        {{for field in form.fields:}}
          {{if form.custom.widget[field]:}}
            {{=form.custom.widget[field].attributes['_name']}} : '',
          {{pass}}
        {{pass}}
    });
    editor.stopEditing();
    userGrid.store.insert(0, u);
    editor.startEditing(0);
}
/**
 * onDelete
 */
function onDelete() {
    var rec = userGrid.getSelectionModel().getSelected();
    if (!rec) {
        return false;
    }
    userGrid.store.remove(rec);
}
