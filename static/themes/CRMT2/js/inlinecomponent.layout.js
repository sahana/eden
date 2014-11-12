/**
 * Example for custom inlinecomponent JS configuration
 * (placeholder to document the pattern, not currently used)
 * 
 * This script should be injected by the S3SQLSubFormLayout custom class
 * (base class in s3forms.py), during __init__, see there for more info
 */
$.inlineComponentLayout = {
    /**
    * Render a read-row (default row layout)
    *
    * @param {string} formname - the form name
    * @param {string|number} rowindex - the row index
    * @param {array} items - the data items
    *
    * @return {jQuery} the row
    */
    renderReadRow: function(formname, rowindex, items) {

        var columns = '';

        // Render the items
        for (var i=0, len=items.length; i<len; i++) {
            columns += '<td>' + items[i] + '</td>';
        }

        // Append edit-button
        if ($('#edt-' + formname + '-none').length !== 0) {
            columns += '<td><div><div id="edt-' + formname + '-' + rowindex + '" class="inline-edt"></div></div></td>';
        } else {
            columns += '<td></td>';
        }

        // Append remove-button
        if ($('#rmv-' + formname + '-none').length !== 0) {
            columns += '<td><div><div id="rmv-' + formname + '-' + rowindex + '" class="inline-rmv"></div></div></td>';
        } else {
            columns += '<td></td>';
        }

        // Get the row
        var rowID = 'read-row-' + formname + '-' + rowindex;
        var row = $('#' + rowID);
        if (!row.length) {
            // New row
            row = $('<tr id="' + rowID + '" class="read-row">');
        }

        // Add the columns to the row
        row.empty().html(columns);

        return row;
    },

    /**
    * Append an error to a form field or row
    *
    * @param {string} formname - the form name
    * @param {string|number} rowindex - the input row index ('none' for add, '0' for edit)
    * @param {string} fieldname - the field name
    * @param {string} message - the error message
    */
    appendError: function(formname, rowindex, fieldname, message) {

        var errorClass = formname + '_error',
            target,
            msg = '<div class="error">' + message + '</div>';

        if (null === fieldname) {
            // Append error message to the whole subform
            if ('none' == rowindex) {
                target = '#add-row-' + formname;
            } else {
                target = '#edit-row-' + formname;
            }
            msg = $('<tr><td colspan="' + $(target + '> td').length + '">' + msg + '</td></tr>');
        } else {
            // Append error message to subform field
            target = '#sub_' + formname + '_' + formname + '_i_' + fieldname + '_edit_' + rowindex;
            msg = $(msg);
        }
        msg.addClass(errorClass).hide().insertAfter(target);
    },

    /**
    * Update (replace) the content of a column, needed to write
    * read-only field data into an edit row
    *
    * @param {jQuery} row - the row
    * @param {number} colIndex - the column index
    * @param {string|HTML} contents - the column contents
    */
    updateColumn: function(row, colIndex, contents) {

        $(row).find('td').eq(colIndex).html(contents);
    },
}
