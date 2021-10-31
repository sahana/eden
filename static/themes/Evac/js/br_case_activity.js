/**
 * Used when creating a Case Activity
 * - Filter Assignee to relevant Handlers
 */

$(document).ready(function() {
    var allHandlers = {},
        handler,
        handlers,
        handlerField = $('#br_case_activity_human_resource_id'),
        handlersLength,
        needField = $('#br_case_activity_need_id'),
        needID;

    var updateHandlers = function() {
        handlersLength = handlers.length;
        handlerField.html('<option value></option>');
        for (i = 0; i < handlersLength; i++) {
            handler = handlers[i];
            opt = '<option value="' + handler.i + '">' + handler.n + '</option>';
            handlerField.append(opt);
        }
    };

    needField.on('change.s3', function() {
            needID = needField.val();
            handlers = allHandlers[needID];
            if (handlers) {
                // We have cached data
                updateHandlers();
            } else {
                // We need to look the data up
                ajaxURL = S3.Ap.concat('/br/need/handlers.json/' + needID);
                $.ajaxS3({
                    url: ajaxURL,
                    dataType: 'json',
                    success: function(data) {
                        allHandlers[needID] = handlers = data;
                        updateHandlers();
                    }
                });
            }
        });

});