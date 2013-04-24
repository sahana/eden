/**
 * Used by the S3LocationSelectorWidget2 (modules/s3/s3widgets.py)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

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

function s3_gis_locationselector2(fieldname, L0, L1, L2, L3, L4, L5) {
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
    // @ToDo: call sub-function
    var values = [];
    for (var id in h) {
        v = h[id];
        v['id'] = id;
        values.push(v);
    }
    values.sort(nameSort);
    // @ToDo: selected
    for (i=0; i < values.length; i++) {
        var location = values[i];
        var option = '<option value="' + location['id'] + '">' + location['n'] + '</option>';
        var level = location['l'];
        if (level == 0) {
            $('#' + fieldname + '_L0').append(option);
        } else if (L0 && (level == 1) && (location['f'] == L0)) {
            $('#' + fieldname + '_L1').append(option);
        } else if (L1 && (level == 2) && (location['f'] == L1)) {
            $('#' + fieldname + '_L2').append(option);
        } else if (L2 && (level == 3) && (location['f'] == L2)) {
            $('#' + fieldname + '_L2').append(option);
        } else if (L3 && (level == 4) && (location['f'] == L3)) {
            $('#' + fieldname + '_L2').append(option);
        } else if (L4 && (level == 5) && (location['f'] == L4)) {
            $('#' + fieldname + '_L2').append(option);
        }
    }
    // Listen events
    $('#' + fieldname + '_L1').change(function() {
        var id = this.value;
        if (id) {
            // Set the real input to this value
            $('#' + fieldname).val(id);
            L1 = id;
            // Do we need to read hierarchy?
            var read = true; 
            for (var id in h) {
                if (h[id].f == L1) {
                    read = false;
                    continue;
                }
            }
            if (read) {
                // AJAX Read extra hierarchy options
                readHierarchy(L1, 2);
            }
            // Populate dropdown
            $('#' + fieldname + '_L2__row').show();
        } else {
            // Clear the real input
            $('#' + fieldname).val('');
            $('#' + fieldname + '_L2__row').hide();
            $('#' + fieldname + '_L3__row').hide();
            $('#' + fieldname + '_L4__row').hide();
            $('#' + fieldname + '_L5__row').hide();
            L2 = L3 = L4 = L5 = null;
        }        
    })
}

function readHierarchy(id, level, fieldname) {
    // Show Throbber
    $('#' + fieldname + '_L' + level + '__throbber').show();
    $.ajax({
        'url': S3.Ap.concat('/gis/hdata/' + id),
        'success': function(data) {
            // Copy the elements across
            for (var prop in n) {
                h[prop] = n[prop];
            }
            // Clear the memory
            n = null;
            lx_select(id, level, fieldname);
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

function lx_select(id, level) {
    // Hierarchical dropdown has been selected
    if (level === 0) {
        // Set Value (to lookup labels later)
        $('#l0_select, #l0_reports, #l0_datas, #l0_analysis1s').val(id);
        // Set Labels
        var h = hdata[id];
        $('#l1 label, #l1_report label, #l1_data label').html(h.l1.toUpperCase() + ':');
        $('#l2 label, #l2_report label, #l2_data label').html(h.l2.toUpperCase() + ':');
        $('#l3 label, #l3_report label, #l3_data label').html(h.l3.toUpperCase() + ':');
        //$('#l4 label, #l4_report label, #l4_data label').html(h.l4.toUpperCase() + ':');
    }
    level = level + 1;
    var l;
    $('#lx_select_throbber, #lx_report_throbber, #lx_data_throbber').hide();
    $('#l' + level + ', #l' + level + '_report, #l' + level + '_data, #l' + level + '_analysis1').show();
    for (l=level + 1; l < 4; l++) {
        $('#l' + l + ', #l' + l + '_report, #l' + l + '_data, #l' + l + '_analysis1').hide();
        $('#l' + l + '_select, #l' + l + '_reports, #l' + l + '_datas, #l' + l + '_analysis1s').val('');
    }
    var values = [];
    var v;
    for (var prop in vdata) {
        v = vdata[prop];
        if (v['f'] == id) {
            v['id'] = prop;
            values.push(v);
        }
    }
    values.sort(nameSort);
    var res, option;
    for (var i=0; i < values.length; i++) {
        v = values[i];
        res = resilienceClass(v['r']);
        option = '<option value="' + v['id'] + '" class="' + res + '">' + v['n'] + '</option>';
        if (analysis) {
            $('#l' + level + '_analysis' + analysis + 's').append(option);
        } else {
            $('#l' + level + '_select, #l' + level + '_reports, #l' + level + '_datas, #l' + level + '_analysis1s').append(option);
        }
    }
}
