// Enable validation errors beside the field globally
Ext.form.Field.prototype.msgTarget = 'side';

var extForm = new Ext.FormPanel({
    standardSubmit: true,
    //title: '{{=T('Login')}}',
    //title: '&nbsp;',
    frame: true,
    bodyStyle:'padding:5px 5px 0',
    width: 350,
    labelWidth: 75, // label settings here cascade unless overridden
    defaults: {width: 230},
    defaultType: 'textfield',
    items: [
        {{for field in form.fields:}}
            {{if form.custom.widget[field]:}}
                {
                    fieldLabel: '{{=form.custom.label[field]}}',
                    name: '{{=form.custom.widget[field].attributes['_name']}}',
                    inputType: '{{=form.custom.widget[field].attributes['_type']}}',
                    id: '{{=form.custom.widget[field].attributes['_id']}}',
                    fieldClass: '{{=form.custom.widget[field].attributes['_class']}}',
                    {{if form.custom.widget[field].attributes.has_key('value'):}}
                        value: '{{=form.custom.widget[field].attributes['value']}}',
                    {{pass}}
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
        new Ext.Container({
                cls: 'hidden',
                items: [
                {{if form.custom.end.components[0][0].attributes['_value']:}}
                    {
                    xtype: 'hidden',
                    name: '_next',
                    value: '{{=form.custom.end.components[0][0].attributes['_value']}}'
                },
                {{pass}}
                    {
                    xtype: 'hidden',
                    name: '_formkey',
                    value: '{{=form.custom.end.components[0][1].attributes['_value']}}'
                }, {
                    xtype: 'hidden',
                    name: '_formname',
                    value: '{{=form.custom.end.components[0][2].attributes['_value']}}'
                }]
            })
    ],

    buttons: [{
        text: '{{=form.custom.submit.attributes['_value']}}',
        handler: function(){
            var fp = this.ownerCt.ownerCt;
            var form = fp.getForm();
            if (form.isValid()) {
                // Check if there are baseParams and if
                // hidden items have been added already
                if (fp.baseParams && !fp.paramsAdded) {
                    // Add hidden items for all baseParams
                    for (i in fp.baseParams) {
                        fp.add({
                            xtype: 'hidden',
                            name: i,
                            value: fp.baseParams[i]
                        });
                    }
                    fp.doLayout();
                    // Set a custom flag to prevent re-adding
                    fp.paramsAdded = true;
                }
                form.action = '';
                form.method = 'POST';
                form.submit();
            }
        }
    }]
});

extForm.render('form-container');
