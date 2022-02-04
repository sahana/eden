$(document).ready(function() {
    var scenarios = $('#scenarios');
    scenarios.on('change', function() {
        // Confirmation Box
        var scenario = $('#scenarios option:selected').attr('label');
        if (confirm(i18n.scenarioConfirm + ' ' + scenario)) {
            // Submit Data
            var url = S3.Ap.concat('/event/incident/' + scenarios.data('incident_id') + '/scenario');
            var options = {
                data: {'scenario_id': scenarios.val()},
                type: 'POST',
                url: url,
                success: function(e) {
                    // Refresh the Page
                    self.location.reload(true);
                }
            };
            $.ajaxS3(options);
            return true;
        } else {
            event.preventDefault();
            return false;
        }
    });
});