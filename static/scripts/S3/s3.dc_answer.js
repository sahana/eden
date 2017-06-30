/* Static JavaScript code for the Answers tab on Data Collection Responses */

S3.dc_grids = function(grids, tablename) {
    if (tablename === undefined) {
        // Assume that fieldnames include the tablename
        tablename = '';
    } else {
        // Prepend fieldnames with the tablename
        tablename = tablename + '_';
    }
    var code,
        field,
        fieldname,
        fields,
        cols,
        cols_length,
        rows,
        grid,
        table;
    for (code in grids) {
        grid = grids[code]
        fields = grid['f'];
        rows = grid['r'];
        rows_length = rows.length;
        cols = grid['c'];
        cols_length = cols.length;
        col_width = Math.floor(12 / (cols_length + 1));
        remainder = 12 - ((cols_length + 1) * col_width);
        // Build the 'Table'
        table = '<div id="' + tablename + code + '" class="row"><div class="row"><div class="small-' + col_width + ' columns">&nbsp;</div>';
        for (var j = 0; j < cols_length; j++) {
            table += '<div class="small-' + col_width + ' columns"><label>' + cols[j] + '</label></div>';
        }
        if (remainder) {
            table += '<div class="small-' + remainder + ' columns">&nbsp;</div>';
        }
        table += '</div>'; // end of Header Row
        for (var i = 0; i < rows_length; i++) {
            table += '<div class="row"><div class="small-' + col_width + ' columns"><label>' + rows[i] + '</label></div>';
            for (var j = 0; j < cols_length; j++) {
                fieldname = fields[j][i];
                if (fieldname) {
                    table += '<div id="' + fieldname + '-here" class="small-' + col_width + ' columns"></div>';
                } else {
                    table += '<div class="small-' + col_width + ' columns">&nbsp;</div>';
                }
            }
            if (remainder) {
                table += '<div class="small-' + remainder + ' columns">&nbsp;</div>';
            }
            table += '</div>'; // end of Row
        }
        table += '</div>'; // end of Table
        // Place it into the correct place
        $('#' + tablename + code + '__row .s3-dummy-field').replaceWith(table);
        // Move the relevant Child Questions to their correct locations
        for (var i = 0; i < rows_length; i++) {
            for (var j = 0; j < cols_length; j++) {
                fieldname = fields[j][i];
                field = $('#' + tablename + fieldname);
                $('#' + fieldname + '-here').append(field);
                // Hide original row
                $('#' + tablename + fieldname + '__row').hide();
            }
        }
    }
}
