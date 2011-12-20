// Helper script to hide the host organisation role if the project
// chosen in the embed-component widget already has a host organisation
// @todo: parametrize!
$(function() {
    hide_host_role =  function(component_id) {
        if (component_id != '') {
            var json_url = S3.Ap.concat('/project/project/' + component_id + '/organisation.s3json?organisation.role=1');
            $.getJSONS3(json_url, function (data) {
                try {
                    project = data["$_project_project"][0];
                    if (project.hasOwnProperty("$_project_organisation")) {
                        $('#project_organisation_role > option[value=1]').hide();
                    }
                    else {
                        $('#project_organisation_role > option[value=1]').show();
                    }
                }
                catch(e) {
                    // skip
                }
            });
        }
        else {
            $('#project_organisation_role > option[value=1]').show();
        }
    };
});
