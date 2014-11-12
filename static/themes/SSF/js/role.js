/**
 * Used to assign Role selected by User   
 */
$(function (){
        
    var _url = window.location.href,
        args = _url.split("/");

    var c = 'project',
        f = 'task',
        id = args[args.indexOf('task') + 1];

   
    $assignBtn = $('#assign-role');
    var mode = $assignBtn.html();
    
    if (mode == i18n.revert_role) {
        $('#role_add').css({
            display: 'none'
        });
    }
    
    $assignBtn.bind('click', function() {
    
        var mode = $assignBtn.html(),
            url;

        var role_id = $('#project_task_role').find(':selected').val(),
            callback;

        if (mode == i18n.assign_role) { 
            url = S3.Ap.concat('/' + c + '/' + f + '/' + id + '/assign.json?action=add');
            callback = function(data) {
                $('#assign-role').html(i18n.revert_role);
                $('#project_task_role').prop('disabled', true);
                $('#role_add').css({
                    display: 'none'
                });
            };
        }
        else {
            url = S3.Ap.concat('/' + c + '/' + f + '/' + id + '/assign.json?action=remove');            
            callback = function(data) {
                $('#assign-role').html(i18n.assign_role);
                $('#project_task_role').prop('disabled', false);
                $('#role_add').css({
                    display: 'inline'
                });
            };
        }
     
        if (role_id != '') {
           
            var data_json = JSON.stringify({'role': role_id});
            $.ajaxS3({
                async: false,
                type: 'POST',
                url: url,
                data: data_json,
                dataType: 'json',
                contentType: 'application/json; charset=utf-8',
                success: callback
            });
        }
    });
});
