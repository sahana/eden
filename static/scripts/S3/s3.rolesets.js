/**
 * Used by S3RoleSetWidget (modules/s3/s3widgets.py)
 */
 
$(function(){
    // Setup multiselect for Orgs
    $('#auth_role_set_orgs_delegated').removeClass('list');
    $('#auth_role_set_orgs_delegated').addClass('multiselect');
    $('#auth_role_set_orgs_delegated').multiselect({
        dividerLocation: 0.5,
        sortable: false
    });
    
    function usersResultParser(data) {
        this.getName = function(index) {
            var item = data[index];
            var name = '';
            if (item.first_name){
                name += ' ' + item.first_name;
            }
            if (item.middle_name){
                name += ' ' + item.middle_name;
            }
            if (item.last_name){
                name += ' ' + item.last_name;
            }
            return name;
        };
        
        search_results = {}
        for (i=0, ii=data.length; i<ii; i++){
            search_results[data[i].id] = {
                selected: false,
                value: this.getName(i)
            }
        }
        return search_results;
    }
    
    // Setup multiselect for Users
    $('#auth_org_role_set_users_assigned').multiselect({
        dividerLocation: 0.5,
        sortable: false
        //itemsCount: '#{count} users selected',
        //remoteUrl: S3.ap.concat('/pr/person/search.json'),
        //remoteParams: {
        //    filter:'~',
        //},
        //dataParser: usersResultParser,
    });

    // Setup form manipulation events
    $('.role_radio_noaccess').click(function() {
        var acl = $.parseJSON(this.id);
        var access = acl[0];
        var reader = acl[1];
        var editor = acl[2];
        $('#rs_' + access).prop('checked', false);
        $('#rs_' + reader).prop('checked', false);
        $('#rs_' + editor).prop('checked', false);
    });

    $('.role_radio_reader').click(function() {
        var acl = $.parseJSON(this.id);
        var access = acl[0];
        var reader = acl[1];
        var editor = acl[2];
        $('#rs_' + access).attr('checked', 'checked');
        $('#rs_' + reader).attr('checked', 'checked');
        $('#rs_' + editor).prop('checked', false);
    });

    $('.role_radio_editor').click(function(){
        var acl = $.parseJSON(this.id);
        var access = acl[0];
        var reader = acl[1];
        var editor = acl[2];
        $('#rs_' + access).attr('checked', 'checked');
        $('#rs_' + reader).prop('checked', false);
        $('#rs_' + editor).attr('checked', 'checked');
    });
});