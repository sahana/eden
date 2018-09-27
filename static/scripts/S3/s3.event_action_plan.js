(function() {
    var refreshDataTables = function() {
        var dt,
            target_id,
            targets = ['profile-list-event_task-1',
                       'profile-list-event_organisation-2',
                       'profile-list-event_human_resource-3',
                       'profile-list-event_asset-4'
                       ];
        for (var i=0, len=targets.length; i < len; i++) {
            target_id = targets[i];
            dt = $('#' + target_id).dataTable();
            dt.fnReloadAjax();
        }
    };
    $(document).ready(function() {
        setInterval(refreshDataTables, 60000);
    });
}());
