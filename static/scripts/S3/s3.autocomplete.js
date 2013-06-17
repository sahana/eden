/**
 * Used by the Autocomplete Widgets (modules/s3/s3widgets.py)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

S3.autocomplete = {};

/**
 * S3AutocompleteWidget
 */
S3.autocomplete.normal = function(fieldname, module, resourcename, input, filter, link, postprocess, delay, min_length) {
    var dummy = 'dummy_' + input;
    var dummy_input = $('#' + dummy);

    if (dummy_input == 'undefined') {
        return;
    }

    var real_input = $('#' + input);
    var throbber = $('#' + dummy + '_throbber');

    var url = S3.Ap.concat('/', module, '/', resourcename, '/search.json?filter=~&field=', fieldname);
    if (filter != 'undefined') {
        url += '&' + filter;
    }
    if ((link != 'undefined') && (link !== '')) {
        url += '&link=' + link;
    }

    // Optional args
    if (postprocess == 'undefined') {
        postprocess = '';
    }
    if (delay == 'undefined') {
        delay = 450;
    }
    if (min_length == 'undefined') {
        min_length = 2;
    }
    var data = {
        val: dummy_input.val(),
        accept: false
    };
    dummy_input.autocomplete({
        delay: delay,
        minLength: min_length,
        source: function(request, response) {
            // Patch the source so that we can handle No Matches
            $.ajax({
                url: url,
                data: {
                    term: request.term
                },
                success: function (data) {
                    if (data.length == 0) {
                        var no_matching_records = i18n.no_matching_records;
                        data.push({
                            id: 0,
                            value: '',
                            label: no_matching_records
                        });
                    }
                    response(data);
                }
            });
        },
        search: function(event, ui) {
            throbber.removeClass('hide').show();
            return true;
        },
        response: function(event, ui, content) {
            throbber.hide();
            return content;
        },
        focus: function(event, ui) {
            dummy_input.val(ui.item[fieldname]);
            return false;
        },
        select: function(event, ui) {
            var item = ui.item;
            if (item.id) {
                dummy_input.val(item[fieldname]);
                real_input.val(item.id)
                          .change();
            } else {
                // No matching results
                dummy_input.val('');
                real_input.val('')
                          .change();
            }
            if (postprocess) {
                // postprocess has to be able to handle the 'no match' option
                eval(postprocess);
            }
            data.accept = true;
            return false;
        }
    })
    .data('ui-autocomplete')._renderItem = function(ul, item) {
        if (item.label) {
            // No Match
            var label = item.label;
        } else {
            var label = item[fieldname];
        }
        return $('<li>').data('item.autocomplete', item)
                        .append('<a>' + label + '</a>')
                        .appendTo(ul);
    };
    // @ToDo: Do this only if new_items=False
    dummy_input.blur(function() {
        if (!dummy_input.val()) {
            real_input.val('');
            data.accept = true;
        }
        if (!data.accept) {
            dummy_input.val(data.val);
        } else {
            data.val = dummy_input.val();
        }
        data.accept = false;
    });
};

/**
 * S3GenericAutocompleteTemplate
 */
S3.autocomplete.generic = function(url, input, name_getter, id_getter, postprocess, delay, min_length) {
    var dummy = 'dummy_' + input;
    var dummy_input = $('#' + dummy);

    if (dummy_input == 'undefined') {
        return;
    }

    var real_input = $('#' + input);
    var throbber = $('#' + dummy + '_throbber');

    // Optional args
    if (name_getter == 'undefined') {
        name_getter = function(item) {
            return item.name;
        }
    }
    if (id_getter == 'undefined') {
        id_getter = function(item) {
            return item.id;
        }
    }
    if (postprocess == 'undefined') {
        postprocess = '';
    }
    if (delay == 'undefined') {
        delay = 450;
    }
    if (min_length == 'undefined') {
        min_length = 2;
    }
    var data = {
        val: dummy_input.val(),
        accept: false
    };
    dummy_input.autocomplete({
        delay: delay,
        minLength: min_length,
        source: function(request, response) {
            // Patch the source so that we can handle No Matches
            $.ajax({
                url: url,
                data: {
                    term: request.term
                },
                success: function (data) {
                    if (data.length == 0) {
                        var no_matching_records = i18n.no_matching_records;
                        data.push({
                            id: 0,
                            value: '',
                            label: no_matching_records
                        });
                    }
                    response(data);
                }
            });
        },
        search: function(event, ui) {
            throbber.removeClass('hide').show();
            return true;
        },
        response: function(event, ui, content) {
            throbber.hide();
            return content;
        },
        focus: function(event, ui) {
            var item = ui.item;
            var name = name_getter(item);
            dummy_input.val(name);
            return false;
        },
        select: function(event, ui) {
            var item = ui.item;
            var id = id_getter(item);
            if (id) {
                var name = name_getter(item);
                dummy_input.val(name);
                real_input.val(id)
                          .change();
            } else {
                // No matching results
                dummy_input.val('');
                real_input.val('')
                          .change();
            }
            if (postprocess) {
                // postprocess has to be able to handle the 'no match' option
                eval(postprocess);
            }
            data.accept = true;
            return false;
        }
    })
    .data('ui-autocomplete')._renderItem = function(ul, item) {
        if (item.label) {
            // No Match
            var label = item.label;
        } else {
            var label = name_getter(item);
        }
        return $('<li>').data('item.autocomplete', item)
                        .append('<a>' + label + '</a>')
                        .appendTo(ul);
    };
    // @ToDo: Do this only if new_items=False
    dummy_input.blur(function() {
        if (!dummy_input.val()) {
            real_input.val('');
            data.accept = true;
        }
        if (!data.accept) {
            dummy_input.val(data.val);
        } else {
            data.val = dummy_input.val();
        }
        data.accept = false;
    });
};

/**
 * S3PersonAutocompleteWidget & hence S3AddPersonWidget
 * - uses first/middle/last
 */
S3.autocomplete.person = function(module, resourcename, input, postprocess, delay, min_length) {
    var dummy = 'dummy_' + input;
    var dummy_input = $('#' + dummy);

    if (dummy_input == 'undefined') {
        return;
    }

    var real_input = $('#' + input);
    var throbber = $('#' + dummy + '_throbber');

    var url = S3.Ap.concat('/', module, '/', resourcename, '/search.json');

    // Optional args
    if (postprocess == 'undefined') {
        postprocess = '';
    }
    if (delay == 'undefined') {
        delay = 450;
    }
    if (min_length == 'undefined') {
        min_length = 2;
    }
    var data = {
        val: dummy_input.val(),
        accept: false
    };
    dummy_input.autocomplete({
        delay: delay,
        minLength: min_length,
        source: function(request, response) {
            // Patch the source so that we can handle No Matches
            $.ajax({
                url: url,
                data: {
                    term: request.term
                },
                success: function (data) {
                    if (data.length == 0) {
                        var no_matching_records = i18n.no_matching_records;
                        data.push({
                            id: 0,
                            value: '',
                            label: no_matching_records,
                            // First Name
                            first: no_matching_records
                        });
                    }
                    response(data);
                }
            });
        },
        search: function(event, ui) {
            throbber.removeClass('hide').show();
            return true;
        },
        response: function(event, ui, content) {
            throbber.hide();
            return content;
        },
        focus: function(event, ui) {
            var item = ui.item;
            var name = item.first;
            if (item.middle) {
                name += ' ' + item.middle;
            }
            if (item.last) {
                name += ' ' + item.last;
            }
            dummy_input.val(name);
            return false;
        },
        select: function(event, ui) {
            var item = ui.item;
            if (item.id) {
                var name = item.first;
                if (item.middle) {
                    name += ' ' + item.middle;
                }
                if (item.last) {
                    name += ' ' + item.last;
                }
                dummy_input.val(name);
                real_input.val(item.id)
                          .change();
            } else {
                // No matching results
                dummy_input.val('');
                real_input.val('')
                          .change();
            }
            if (postprocess) {
                // postprocess has to be able to handle the 'no match' option
                eval(postprocess);
            }
            data.accept = true;
            return false;
        }
    })
    .data('ui-autocomplete')._renderItem = function(ul, item) {
        var name = item.first;
        if (item.middle) {
            name += ' ' + item.middle;
        }
        if (item.last) {
            name += ' ' + item.last;
        }
        return $('<li>').data('item.autocomplete', item)
                        .append('<a>' + name + '</a>')
                        .appendTo(ul);
    };
    // @ToDo: Do this only if new_items=False
    dummy_input.blur(function() {
        if (!dummy_input.val()) {
            real_input.val('');
            data.accept = true;
        }
        if (!data.accept) {
            dummy_input.val(data.val);
        } else {
            data.val = dummy_input.val();
        }
        data.accept = false;
    });
};

/**
 * S3HumanResourceAutocompleteWidget
 * - uses first/middle/last, organisation & job role
 */
S3.autocomplete.hrm = function(group, input, postprocess, delay, min_length) {
    var dummy = 'dummy_' + input;
    var dummy_input = $('#' + dummy);

    if (dummy_input == 'undefined') {
        return;
    }

    var real_input = $('#' + input);
    var throbber = $('#' + dummy + '_throbber');

    if (group == "staff") {
        // Search Staff using S3HRSearch
        var url = S3.Ap.concat('/hrm/person_search/search.json?group=staff');
    } else if (group == "volunteer") {
        // Search Volunteers using S3HRSearch
        var url = S3.Ap.concat('/vol/person_search/search.json');
    } else {
        // Search all HRs using S3HRSearch
        var url = S3.Ap.concat('/hrm/person_search/search.json');
    }

    // Optional args
    if (postprocess == 'undefined') {
        postprocess = '';
    }
    if (delay == 'undefined') {
        delay = 450;
    }
    if (min_length == 'undefined') {
        min_length = 2;
    }
    var data = {
        val: dummy_input.val(),
        accept: false
    };
    dummy_input.autocomplete({
        delay: delay,
        minLength: min_length,
        source: function(request, response) {
            // Patch the source so that we can handle No Matches
            $.ajax({
                url: url,
                data: {
                    term: request.term
                },
                success: function (data) {
                    if (data.length == 0) {
                        var no_matching_records = i18n.no_matching_records;
                        data.push({
                            id: 0,
                            value: '',
                            label: no_matching_records,
                            // First Name
                            first: no_matching_records
                        });
                    }
                    response(data);
                }
            });
        },
        search: function(event, ui) {
            throbber.removeClass('hide').show();
            return true;
        },
        response: function(event, ui, content) {
            throbber.hide();
            return content;
        },
        focus: function(event, ui) {
            var item = ui.item;
            var name = item.first;
            if (item.middle) {
                name += ' ' + item.middle;
            }
            if (item.last) {
                name += ' ' + item.last;
            }
            var org = item.org;
            var job = item.job;
            if (org || job) {
                if (job) {
                    name += ' (' + job;
                    if (org) {
                        name += ', ' + org;
                    }
                    name += ')';
                } else {
                    name += ' (' + org + ')';
                }
            }
            dummy_input.val(name);
            return false;
        },
        select: function(event, ui) {
            var item = ui.item;
            if (item.id) {
                var name = item.first;
                if (item.middle) {
                    name += ' ' + item.middle;
                }
                if (item.last) {
                    name += ' ' + item.last;
                }
                var org = item.org;
                var job = item.job;
                if (org || job) {
                    if (job) {
                        name += ' (' + job;
                        if (org) {
                            name += ', ' + org;
                        }
                        name += ')';
                    } else {
                        name += ' (' + org + ')';
                    }
                }
                dummy_input.val(name);
                real_input.val(item.id)
                          .change();
            } else {
                // No matching results
                dummy_input.val('');
                real_input.val('')
                          .change();
            }
            if (postprocess) {
                // postprocess has to be able to handle the 'no match' option
                eval(postprocess);
            }
            data.accept = true;
            return false;
        }
    })
    .data('ui-autocomplete')._renderItem = function(ul, item) {
        var name = item.first;
        if (item.middle) {
            name += ' ' + item.middle;
        }
        if (item.last) {
            name += ' ' + item.last;
        }
        var org = item.org;
        var job = item.job;
        if (org || job) {
            if (job) {
                name += ' (' + job;
                if (org) {
                    name += ', ' + org;
                }
                name += ')';
            } else {
                name += ' (' + org + ')';
            }
        }
        return $('<li>').data('item.autocomplete', item)
                        .append('<a>' + name + '</a>')
                        .appendTo(ul);
    };
    // @ToDo: Do this only if new_items=False
    dummy_input.blur(function() {
        if (!dummy_input.val()) {
            real_input.val('');
            data.accept = true;
        }
        if (!data.accept) {
            dummy_input.val(data.val);
        } else {
            data.val = dummy_input.val();
        }
        data.accept = false;
    });
};

/**
 * S3SiteAutocompleteWidget
 * - uses name & type
 */
S3.autocomplete.site = function(input, postprocess, delay, min_length) {
    var dummy = 'dummy_' + input;
    var dummy_input = $('#' + dummy);

    if (dummy_input == 'undefined') {
        return;
    }

    var real_input = $('#' + input);
    var throbber = $('#' + dummy + '_throbber');

    var url = S3.Ap.concat('/org/site/search.json?field=name&filter=~');

    // Optional args
    if (postprocess == 'undefined') {
        postprocess = '';
    }
    if (delay == 'undefined') {
        delay = 450;
    }
    if (min_length == 'undefined') {
        min_length = 2;
    }
    var data = {
        val: dummy_input.val(),
        accept: false
    };
    dummy_input.autocomplete({
        delay: delay,
        minLength: min_length,
        source: function(request, response) {
            // Patch the source so that we can handle No Matches
            $.ajax({
                url: url,
                data: {
                    term: request.term
                },
                success: function (data) {
                    if (data.length == 0) {
                        var no_matching_records = i18n.no_matching_records;
                        data.push({
                            id: 0,
                            value: '',
                            label: no_matching_records,
                            name: no_matching_records
                        });
                    }
                    response(data);
                }
            });
        },
        search: function(event, ui) {
            throbber.removeClass('hide').show();
            return true;
        },
        response: function(event, ui, content) {
            throbber.hide();
            return content;
        },
        focus: function(event, ui) {
            var item = ui.item;
            var name = item.name || '';
            if (item.instance_type) {
                name += ' (' + S3.org_site_types[item.instance_type] + ')';
            }
            dummy_input.val(name);
            return false;
        },
        select: function(event, ui) {
            var item = ui.item;
            if (item.id) {
                var name = item.name || '';
                if (item.instance_type) {
                    name += ' (' + S3.org_site_types[item.instance_type] + ')';
                }
                dummy_input.val(name);
                real_input.val(item.id)
                          .change();
            } else {
                // No matching results
                dummy_input.val('');
                real_input.val('')
                          .change();
            }
            if (postprocess) {
                // postprocess has to be able to handle the 'no match' option
                eval(postprocess);
            }
            data.accept = true;
            return false;
        }
    })
    .data('ui-autocomplete')._renderItem = function(ul, item) {
        var name = item.name || '';
        if (item.instance_type) {
            name += ' (' + S3.org_site_types[item.instance_type] + ')';
        }
        return $('<li>').data('item.autocomplete', item)
                        .append('<a>' + name + '</a>')
                        .appendTo(ul);
    };
    // @ToDo: Do this only if new_items=False
    dummy_input.blur(function() {
        if (!dummy_input.val()) {
            real_input.val('');
            data.accept = true;
        }
        if (!data.accept) {
            dummy_input.val(data.val);
        } else {
            data.val = dummy_input.val();
        }
        data.accept = false;
    });
};

/**
 * S3SiteAddressAutocompleteWidget
 * - uses name & address (address added to represent server-side)
 */
S3.autocomplete.site_address = function(input, postprocess, delay, min_length) {
    var dummy = 'dummy_' + input;
    var dummy_input = $('#' + dummy);

    if (dummy_input == 'undefined') {
        return;
    }

    var real_input = $('#' + input);
    var throbber = $('#' + dummy + '_throbber');

    // Address arg tells controller to use S3SiteAddressSearch
    var url = S3.Ap.concat('/org/site/search.json/address?field=name&filter=~');

    // Optional args
    if (postprocess == 'undefined') {
        postprocess = '';
    }
    if (delay == 'undefined') {
        delay = 450;
    }
    if (min_length == 'undefined') {
        min_length = 2;
    }
    var data = {
        val: dummy_input.val(),
        accept: false
    };
    dummy_input.autocomplete({
        delay: delay,
        minLength: min_length,
        source: function(request, response) {
            // Patch the source so that we can handle No Matches
            $.ajax({
                url: url,
                data: {
                    term: request.term
                },
                success: function (data) {
                    if (data.length == 0) {
                        var no_matching_records = i18n.no_matching_records;
                        data.push({
                            id: 0,
                            value: '',
                            label: no_matching_records,
                            name: no_matching_records
                        });
                    }
                    response(data);
                }
            });
        },
        search: function(event, ui) {
            throbber.removeClass('hide').show();
            return true;
        },
        response: function(event, ui, content) {
            throbber.hide();
            return content;
        },
        focus: function(event, ui) {
            var name = ui.item.name || '';
            dummy_input.val(name);
            return false;
        },
        select: function(event, ui) {
            var item = ui.item;
            if (item.id) {
                var name = item.name || '';
                dummy_input.val(name);
                real_input.val(item.id)
                          .change();
            } else {
                // No matching results
                dummy_input.val('');
                real_input.val('')
                          .change();
            }
            if (postprocess) {
                // postprocess has to be able to handle the 'no match' option
                eval(postprocess);
            }
            data.accept = true;
            return false;
        }
    })
    .data('ui-autocomplete')._renderItem = function(ul, item) {
        var name = item.name || '';
        return $('<li>').data('item.autocomplete', item)
                        .append('<a>' + name + '</a>')
                        .appendTo(ul);
    };
    // @ToDo: Do this only if new_items=False
    dummy_input.blur(function() {
        if (!dummy_input.val()) {
            real_input.val('');
            data.accept = true;
        }
        if (!data.accept) {
            dummy_input.val(data.val);
        } else {
            data.val = dummy_input.val();
        }
        data.accept = false;
    });
};

// END ========================================================================