/**
 * Used by data lists (views/datalist.html)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

function dlURLAppend(url, query) {
    // Append extra query elements to a URL
    
    var parts = url.split('?'), q = '';
    var newurl = parts[0];
    if (parts.length > 1) {
        if (query) {
            q = '&' + query;
        }
        return (newurl + '?' + parts[1] + q);
    } else {
        if (query) {
            q = '?' + query;
        }
        return (newurl + q);
    }
}

function dlAjaxRemoveItemBind() {
    // Bind the click-event handler to dl-item-delete elements

    $('.dl-item-delete').css({cursor: 'pointer'});
    $('.dl-item-delete').click(function(event) {
        if (confirm(i18n.delete_confirmation)) {
            dlAjaxRemoveItem(this);
            return true;
        } else {
            event.preventDefault();
            return false;
        }
    });
}

function dlAutoRetrieve(item) {
    // Force page retrieval
    $(item).closest('.dl').infinitescroll('retrieve');
}

function dlAjaxReloadItem(list_id, record_id) {
    // Ajax-reload a single item in a datalist (e.g. after update)

    datalist = '#' + list_id;
    var item_id = '#' + list_id + '-' + record_id;

    var pagination = $(datalist).find('input.dl-pagination');
    if (!pagination.length) {
        // No such datalist or no pagination data
        return;
    }
    var dl_data = JSON.parse($(pagination[0]).val());

    // Do we have an Ajax-URL?
    var ajaxurl = dl_data['ajaxurl'];
    if (ajaxurl === null) {
        return;
    }

    // Is the item currently loaded?
    var item = $(item_id);
    if (!item.length) {
        return;
    }

    // Ajax-load the item
    $.ajax({
        'url': dlURLAppend(ajaxurl, 'record=' + record_id),
        'success': function(data) {
            var item_data = $(data.slice(data.indexOf('<'))).find(item_id);
            if (item_data.length) {
                $(item).replaceWith(item_data);
            }
        },
        'error': function(request, status, error) {
            if (error == 'UNAUTHORIZED') {
                msg = i18n.gis_requires_login;
            } else {
                msg = request.responseText;
            }
            console.log(msg);
        },
        'dataType': 'html'
    });
}

function dlAjaxRemoveItem(anchor) {
    // Ajax-delete and remove an item from the list

    var item = $(anchor).closest('.dl-item');
    if (!item.length) {
        return;
    }
    var item_id = $(item).attr('id');
    var record_id = item_id.split('-').pop();

    var datalist = $(item).closest('.dl');
    var pagination = $(datalist).find('input.dl-pagination');
    if (!pagination.length) {
        // No such datalist or no pagination data
        return;
    }
    var dl_data = JSON.parse($(pagination[0]).val());

    // Do we have an Ajax-URL?
    var ajaxurl = dl_data['ajaxurl'];
    if (ajaxurl === null) {
        return;
    }

    // Ajax-delete the item
    $.ajax({
        'url': dlURLAppend(ajaxurl, 'delete=' + record_id),
        'success': function(data) {
            $(item).remove();
        },
        'error': function(request, status, error) {
            var msg;
            if (error == 'UNAUTHORIZED') {
                msg = i18n.gis_requires_login;
            } else {
                msg = request.responseText;
            }
            console.log(msg);
        },
        'type': 'POST',
        'dataType': 'json'
    });
    $(datalist).find('.dl-item:last:in-viewport').each(function() {
        $(this).addClass('autoretrieve');
        dlAutoRetrieve(this);
    });
}

function dlAjaxReload(list_id) {
    // Reload the data list (also resets pagination to page #1)

    datalist = $('#' + list_id);
    if (!datalist.length) {
        return;
    }
    
    var pagination = $(datalist).find('input.dl-pagination');
    if (!pagination.length) {
        // No pagination
        return;
    }
    var dl_data = JSON.parse($(pagination[0]).val());

    // Read dl_data
    var startindex = dl_data['startindex'],
        pagesize = dl_data['pagesize'],
        ajaxurl = dl_data['ajaxurl'];

    if (pagesize === null) {
        // No pagination
        return;
    }

    var start = startindex;
    var limit = pagesize;

    // Ajax-load the item
    $.ajax({
        'url': dlURLAppend(ajaxurl, 'start=' + startindex + '&limit=' + pagesize),
        'success': function(data) {
            var newlist = $(data.slice(data.indexOf('<'))).find('.dl');
            $(datalist).infinitescroll('destroy');
            $(datalist).data('infinitescroll', null);
            $(datalist).empty().append(newlist);
            $(datalist).find('input.dl-pagination').replaceWith(pagination);
            dlInfiniteScroll(datalist);
            $(datalist).find('.dl-item:last:in-viewport').each(function() {
                $(this).addClass('autoretrieve');
                dlAutoRetrieve(this);
            });
        },
        'error': function(request, status, error) {
            if (error == 'UNAUTHORIZED') {
                msg = i18n.gis_requires_login;
            } else {
                msg = request.responseText;
            }
            console.log(msg);
        },
        'dataType': 'html'
    });
}

function dlInfiniteScroll(datalist) {
    // Activate infinite scroll pagination

    var pagination = $(datalist).find('input.dl-pagination');
    if (!pagination.length) {
        // No pagination
        return;
    }
    var dl_data = JSON.parse($(pagination[0]).val());

    // Read dl_data
    var startindex = dl_data['startindex'],
        maxitems = dl_data['maxitems'],
        pagesize = dl_data['pagesize'],
        ajaxurl = dl_data['ajaxurl'];

    if (pagesize === null) {
        // No pagination
        return;
    }

    // Compute bounds
    var maxindex = startindex + maxitems,
        initialitems = $(datalist).find('.dl-item').length;

    // Compute maxpage
    var maxpage = 1, ajaxitems = (maxitems - initialitems);
    if ( ajaxitems > 0) {
        maxpage += Math.ceil(ajaxitems / pagesize);
    } else {
        if (pagination.length) {
            pagination.css({display:'none'});
        }
        return;
    }

    if (pagination.length) {
        $(datalist).infinitescroll({
                debug: false,
                loading: {
                    finishedMsg: "no more items to load",
                    msgText: "loading...",
                    img: S3.Ap.concat('/static/img/indicator.gif')
                },
                navSelector: "div.dl-navigation",
                nextSelector: "div.dl-navigation a:first",
                itemSelector: "div.dl-item",
                path: function(page) {
                    // Compute start+limit
                    var start = initialitems + (page - 2) * pagesize;
                    var limit = Math.min(pagesize, maxindex - start);
                    // Construct Ajax URL
                    var url = dlURLAppend(ajaxurl, 'start=' + start + '&limit=' + limit);
                    return url;
                },
                maxPage: maxpage

            },
            function(data) {
                $('.dl').each(function() {
                    $(this).find('.dl-item:last:in-viewport').each(function() {
                        if (!$(this).hasClass('autoretrieve')) {
                            $(this).addClass('autoretrieve');
                            dlAutoRetrieve(this);
                        }
                    });
                });
                // Re-bind the click-event to newly loaded dl-item-delete's
                $('.dl-item-delete').unbind('click');
                dlAjaxRemoveItemBind();
            }
        );
    }
}

$(document).ready(function() {

    $('.dl').each(function() {
        dlInfiniteScroll(this);
    });
    $('.dl').each(function() {
        $(this).find('.dl-item:last:in-viewport').each(function() {
            $(this).addClass('autoretrieve');
            dlAutoRetrieve(this);
        });
    });
    dlAjaxRemoveItemBind();
});

// END ========================================================================
