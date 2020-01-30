/**
 * Dynamically update list of templates when repo is changed
 */

// Module pattern to hide internal vars
(function() {
    var get_templates = function(repo_url) {
        // Download templates.json
        // - currently assumes that repo is hosted on GitHub!
        var parts = repo_url.split('/'),
            repo_owner = parts[3],
            repo = parts[4],
            templates_url = 'https://raw.githubusercontent.com/' + repo_owner + '/' + repo + '/master/modules/templates/templates.json';
        $.getJSONS3(templates_url, function(templates) {
            var options = [],
                widget = $('#setup_deployment_template'),
                // Store current value of dropdown (to set again, if we can)
                current_value = widget.val();
            for (var t in templates) {
                if (templates.hasOwnProperty(t)) {
                    options.push('<option value="' + t + '">' + templates[t] + '</option>');
                }
            }
            widget.html(options.join(''))
                   .val(current_value);
        });
    }

    $(document).ready(function() {
        // Listen for changes
        $('#setup_deployment_repo_url').on('change.eden', function() {
            get_templates($(this).val());
        });

    });

})(jQuery);