/**
 * Custom S3SQLInlineComponent JS configuration
 *
 * This script is injected by settings.ui.inline_component_layout
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

        var buttons = [];
        if ($('#edt-' + formname + '-none').length !== 0) {
            buttons.push('<div><div id="edt-' + formname + '-' + rowindex + '" class="inline-edt"></div></div>');
        }
        if ($('#rmv-' + formname + '-none').length !== 0) {
            buttons.push('<div><div id="rmv-' + formname + '-' + rowindex + '" class="inline-rmv"></div></div>');
        }

        // Render the items
        var addColumns = $('#add-row-' + formname).find('.columns'),
            classes,
            classList;
        for (var i=0, len=items.length; i<len; i++) {
            // Get the column-classes from the add-row
            classes = [];
            if (addColumns.length) {
                classList = addColumns.eq(i).attr('class').split(/\s+/);
                $.each(classList, function(index, item) {
                    if (item.substring(0, 5) == 'small') {
                        classes.push(item);
                    }
                });
                classes.push('columns');
            } else {
                classes.push('small-1 columns');
            }
            // Last item should have 'end' class unless we have buttons
            if (!buttons && i == len-1) {
                classes.push('end');
            }
            columns += '<div class="' + classes.join(' ') + '">' + items[i] + '</div>';
        }
        if (buttons) {
            columns += '<div class="inline-actions small-1 columns end">' + buttons.join("") + '</div>';
        }

        // Get the row
        var rowID = 'read-row-' + formname + '-' + rowindex;
        var row = $('#' + rowID);
        if (!row.length) {
            // New row
            row = $('<div id="' + rowID + '" class="read-row row">');
        }

        // Add the columns to the row
        row.empty().html(columns);

        return row;
    },

    /**
        * Append a new read-row to the inline component
        *
        * @param {string} formname - the formname
        * @param {jQuery} row - the row to append
        */
    appendReadRow: function(formname, row) {

        $('#sub-' + formname + ' > .embeddedComponent > .inline-items').append(row);
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
            // Determine the total column width
            var targetColumns = $(target).find('.columns'),
                width = 0,
                columnWidth,
                classList;
            for (var i=0, len=targetColumns.length; i<len; i++) {
                classList = targetColumns.eq(i).attr('class').split(/\s+/);
                $.each(classList, function(index, item) {
                    if (item.substring(0, 5) == 'small') {
                        columnWidth = parseInt(item.substring(6));
                        if (columnWidth) {
                            width += columnWidth;
                        }
                    }
                });
            }
            if (width === 0) {
                width = 12;
            }
            // Render the message and insert after current row
            msg = $('<div class="row"><div class="small-' + width + ' columns">' + msg + '</div></div>');
            msg.addClass(errorClass).hide().insertAfter(target);
        } else {
            // Append the message to subform column
            target = '#sub_' + formname + '_' + formname + '_i_' + fieldname + '_edit_' + rowindex;
            msg = $(msg).addClass(errorClass).hide();
            $(target).parent().append(msg);
        }
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

        $(row).find('div.columns').eq(colIndex).html(contents);
    },
}
