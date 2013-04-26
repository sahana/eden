/**
 * Used by the S3LocationSelectorWidget2 (modules/s3/s3widgets.py)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 *
 * Globals
 *  Location Hierachy
 *  l = {id : {'n' : name,
 *             'l' : level,
 *             'f' : parent
 *             }}
 *  n = same but temporary for new content retrieved from /gis/ldata
 *  hdata = Labels Hierarchy (@ToDo)
 */

function s3_gis_locationselector2(fieldname, L0, L1, L2, L3, L4, L5) {
    // Function to be called by S3LocationSelectorWidget2

    // Move the visible rows underneath the real one
    var L0_row = $('#' + fieldname + '_L0__row').clone();
    var L1_row = $('#' + fieldname + '_L1__row').clone();
    var L2_row = $('#' + fieldname + '_L2__row').clone();
    var L3_row = $('#' + fieldname + '_L3__row').clone();
    var L4_row = $('#' + fieldname + '_L4__row').clone();
    var L5_row = $('#' + fieldname + '_L5__row').clone();
    $('#' + fieldname + '__row').hide()
                                .after(L5_row)
                                .after(L4_row)
                                .after(L3_row)
                                .after(L2_row)
                                .after(L1_row)
                                .after(L0_row);
    $('#' + fieldname + '__row div.controls div:eq(1)').remove();

    // Initial population of dropdown(s)
    if (L0) {
        lx_select(fieldname, 0, L0);
    }
    if (L1) {
        lx_select(fieldname, 1, L1);
    }
    if (L2) {
        lx_select(fieldname, 2, L2);
    }
    if (L3) {
        lx_select(fieldname, 3, L3);
    }
    if (L4) {
        lx_select(fieldname, 4, L4);
    }
    if (L5) {
        lx_select(fieldname, 5, L5);
    }

    // Listen events
    $('#' + fieldname + '_L0').change(function() {
        lx_select(fieldname, 0);
    });
    $('#' + fieldname + '_L1').change(function() {
        lx_select(fieldname, 1);
    });
    $('#' + fieldname + '_L2').change(function() {
        lx_select(fieldname, 2);
    });
    $('#' + fieldname + '_L3').change(function() {
        lx_select(fieldname, 3);
    });
    $('#' + fieldname + '_L4').change(function() {
        lx_select(fieldname, 4);
    });
    $('#' + fieldname + '_L5').change(function() {
        lx_select(fieldname, 5);
    });
}

function lx_select(fieldname, level, id) {
    // Hierarchical dropdown has been selected
    if (!id) {
        id = $('#' + fieldname + '_L' + level).val();
    }
    if (level === 0) {
        // @ToDo: This data structure doesn't exist yet (not required for TLDRMP)
        // Set Labels
        //var h = hdata[id];
        //$('#' + fieldname + '_L1__row label').html(h.l1 + ':');
        //$('#' + fieldname + '_L2__row label').html(h.l2 + ':');
        //$('#' + fieldname + '_L3__row label').html(h.l3 + ':');
        //$('#' + fieldname + '_L4__row label').html(h.l4 + ':');
        //$('#' + fieldname + '_L5__row label').html(h.l5 + ':');
    }
    if (id) {
        // Set the real input to this value
        $('#' + fieldname).val(id);
        // Show next dropdown
        level += 1;
        $('#' + fieldname + '_L' + level + '__row').show();
        // Do we need to read hierarchy?
        var read = true; 
        for (var i in l) {
            if (l[i].f == id) {
                read = false;
                continue;
            }
        }
        if (read) {
            // AJAX Read extra hierarchy options
            readHierarchy(fieldname, level, id);
        }
        var values = [];
        for (var i in l) {
            v = l[i];
            if ((v['l'] == level) && (v['f'] == id)) {
                v['i'] = i;
                values.push(v);
            }
        }
        values.sort(nameSort);
        var _id, location, option, selected;
        for (var i=0; i < values.length; i++) {
            location = values[i];
            _id = location['i'];
            if (id == _id) {
                selected = ' selected="selected"';
            } else {
                selected = '';
            }
            option = '<option value="' + _id + '"' + selected + '>' + location['n'] + '</option>';
            $('#' + fieldname + '_L' + level).append(option);
        }
    } else {
        if (level === 0) {
            // Clear the real input
            $('#' + fieldname).val('');
        } else {
            // Set the real input to the next higher-level
            id = $('#' + fieldname + '_L' + (level - 1)).val();
            $('#' + fieldname).val(id);
        }
        // Hide all lower levels
        for (var lev=level + 1; lev < 6; lev++) {
            $('#' + fieldname + '_L' + lev + '__row').hide();
        }
    }
}

function nameSort(a, b) {
    // Sort Hierarchical Dropdown data by Name
    a = a['n'];
    var names = [a, b['n']];
    names.sort();
    if (names[0] == a) {
        return -1;
    } else {
        return 1;
    }
}

function readHierarchy(fieldname, level, id) {
    // Show Throbber
    $('#' + fieldname + '_L' + level + '__throbber').show();
    // Download Location Data
    $.ajax({
        'async': false,
        'url': S3.Ap.concat('/gis/ldata/' + id),
        'success': function(data) {
            // Copy the elements across
            for (var prop in n) {
                l[prop] = n[prop];
            }
            // Clear the memory
            n = null;
            // Hide Throbber
            $('#' + fieldname + '_L' + level + '__throbber').hide();
        },
        'error': function(request, status, error) {
            if (error == 'UNAUTHORIZED') {
                msg = i18n.gis_requires_login;
            } else {
                msg = request.responseText;
            }
        },
        'dataType': 'script'
    });
}
