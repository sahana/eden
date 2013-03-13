/**
 * Used by data lists (views/datalist.html)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

/*
 * dlURLAppend: Helper function to extend a URL with a query
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

/*
 * dlItemBindEvents: Bind event handlers for item actions
 */
function dlItemBindEvents() {

    // Click-event for dl-item-delete
    $('.dl-item-delete').css({cursor: 'pointer'});
    $('.dl-item-delete').unbind('click');
    $('.dl-item-delete').click(function(event) {
        if (confirm(i18n.delete_confirmation)) {
            dlAjaxDeleteItem(this);
            return true;
        } else {
            event.preventDefault();
            return false;
        }
    });

    // Modals
    S3.addModals();
}

/*
 * dlAutoRetrieve: Force retrieval of the next scroll page
 */
function dlAutoRetrieve(item) {
    // Force page retrieval
    $(item).closest('.dl').infinitescroll('retrieve');
}

/*
 * dlAjaxReloadItem: Ajax-reload a single item in a datalist (e.g. after update)
 */
function dlAjaxReloadItem(list_id, record_id) {

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
            dlItemBindEvents();
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

/*
 * dlAjaxDeleteItem: Ajax-delete an item from a datalist
 */
function dlAjaxDeleteItem(anchor) {

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

/*
 * dlAjaxReload: Force Ajax-reload of a datalist
 */
function dlAjaxReload(list_id, filters) {

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
        maxitems = dl_data['maxitems'],
        totalitems = dl_data['totalitems'],
        ajaxurl = dl_data['ajaxurl'];

    if (filters) {
        try {
            ajaxurl = S3.search.filterURL(ajaxurl, filters);
            dl_data['ajaxurl'] = ajaxurl;
            $(pagination[0]).val(JSON.stringify(dl_data));
        } catch(e) {}
    }

    if (pagesize === null) {
        // No pagination
        return;
    }

    var start = startindex;
    var limit = pagesize;

    // Ajax-load the list
    $.ajax({
        'url': dlURLAppend(ajaxurl, 'start=' + startindex + '&limit=' + pagesize),
        'success': function(data) {
            var newlist = $(data.slice(data.indexOf('<'))).find('.dl');
            $(datalist).infinitescroll('destroy');
            $(datalist).data('infinitescroll', null);
            if (newlist.length) {
                var pagination_new = $(newlist).find('input.dl-pagination');
                if (pagination_new.length) {
                    var dl_data_new = JSON.parse($(pagination_new[0]).val());
                    dl_data['totalitems'] = dl_data_new['totalitems'];
                    $(pagination[0]).val(JSON.stringify(dl_data));
                }
                $(datalist).empty().html(newlist.html());
                $(datalist).find('input.dl-pagination').replaceWith(pagination);
            } else {
                // List is empty
                var nav = $(datalist).find('.dl-navigation').css({display: 'none'});
                newlist = $(data.slice(data.indexOf('<'))).find('.empty');
                $(datalist).empty().append(newlist);
                $(datalist).append(nav);
            }
            dlInfiniteScroll(datalist);
            $(datalist).find('.dl-item:last:in-viewport').each(function() {
                $(this).addClass('autoretrieve');
                dlAutoRetrieve(this);
            });
            dlItemBindEvents();
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

/*
 * dlInfiniteScroll: activate infinite scroll pagination
 */
function dlInfiniteScroll(datalist) {

    var pagination = $(datalist).find('input.dl-pagination');
    if (!pagination.length) {
        // No pagination
        return;
    }
    var dl_data = JSON.parse($(pagination[0]).val());

    // Read dl_data
    var startindex = dl_data['startindex'],
        maxitems = dl_data['maxitems'],
        totalitems = dl_data['totalitems'],
        pagesize = dl_data['pagesize'],
        ajaxurl = dl_data['ajaxurl'];

    if (pagesize === null) {
        // No pagination
        pagination.closest('.dl-navigation').css({display:'none'});
        return;
    }

    // Cannot retrieve more items than there are totally available
    maxitems = Math.min(maxitems, totalitems - startindex);

    // Compute bounds
    var maxindex = startindex + maxitems,
        initialitems = $(datalist).find('.dl-item').length;

    // Compute maxpage
    var maxpage = 1, ajaxitems = (maxitems - initialitems);
    if ( ajaxitems > 0) {
        maxpage += Math.ceil(ajaxitems / pagesize);
    } else {
        if (pagination.length) {
            pagination.closest('.dl-navigation').css({display:'none'});
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
                dlItemBindEvents();
            }
        );
    }
}

/*
 * DataLists document-ready script
 */
$(document).ready(function() {

    // Initialize infinite scroll
    $('.dl').each(function() {
        dlInfiniteScroll(this);
    });

    // Auto-retrieve paginated lists which don't reach their view-port bottom
    $('.dl').each(function() {
        $(this).find('.dl-item:last:in-viewport').each(function() {
            $(this).addClass('autoretrieve');
            dlAutoRetrieve(this);
        });
    });

    // Bind events for newly loaded items
    dlItemBindEvents();
});

// END ========================================================================
