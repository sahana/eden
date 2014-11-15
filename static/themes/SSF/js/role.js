/**
* Used to assign Role selected by User
*/
$(function (){
    var $assignBtn = $('#assign-role');

    $assignBtn.bind('click', function() {

        var url,
            type,
            data_json,
            mode = $('#assign-role span').html();

        if (mode == i18n.assign_role) {
            // Assign 'Watch' Role
            var task_uuid = $assignBtn.attr('data-task_uuid'),
                role_uuid = $assignBtn.attr('data-role_uuid');

            type = 'PUT';
            url = S3.Ap.concat('/project/member.s3json');
            data_json = {'$_project_member':[{'$k_task_id':{'@resource':'project_task',
                                                            '@uuid':task_uuid},
                                              '$k_role_id':{'@resource':'project_role',
                                                            '@uuid':role_uuid}
                                             }],
                         '$_project_task':[{'@uuid':task_uuid}],
                         '$_project_role':[{'@uuid':role_uuid}]
                         };
            data_json = JSON.stringify(data_json);
            callback = function(result) {
                if (result['status'] == 'success') {
                    new_id = result['created'][0];
                    $assignBtn.attr('data-id', new_id);
                    $assignBtn.html('<i class="icon-eye-close"></i><span>' + i18n.revert_role + '</span>');
                }
            };
        }
        else {
            // Revert Role
            type = 'DELETE';    
            resource_url = $assignBtn.attr('data-url');
            member_id = $assignBtn.attr('data-id');
            url = S3.Ap.concat(resource_url + member_id);
            callback = function(result) {
                if (result['status'] == 'success') {
                    $assignBtn.attr('data-id', 'null');
                    $assignBtn.html('<i class="icon-eye-open"></i><span>' + i18n.assign_role + '</span>');
                }
            };
        }
        $.ajaxS3({
            async: false,
            type: type,
            url: url,
            data: data_json,
            dataType: 'json',
            contentType: 'application/json; charset=utf-8',
            success: callback
        });
    });
});
