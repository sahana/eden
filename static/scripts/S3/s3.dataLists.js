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

    var parts = url.split('?'),
        q = '';
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
    $('.dl-item-delete').css({cursor: 'pointer'})
                        .unbind('click')
                        .click(function(event) {
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
function dlAutoRetrieve(row) {
    // Force page retrieval
    $(row).closest('.dl').infinitescroll('retrieve');
}

/*
 * dlAjaxReloadItem: Ajax-reload a single item in a datalist (e.g. after update)
 */
function dlAjaxReloadItem(list_id, record_id) {

    var datalist = '#' + list_id;
    var pagination = $(datalist).find('input.dl-pagination');
    if (!pagination.length) {
        // No such datalist or no pagination data
        return;
    }

    // Do we have an Ajax-URL?
    var dl_data = JSON.parse($(pagination[0]).val());
    var ajaxurl = dl_data['ajaxurl'];
    if (ajaxurl === null) {
        return;
    }

    // Is the item currently loaded?
    var item_id = '#' + list_id + '-' + record_id;
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
                item.replaceWith(item_data);
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
    var $item = $(item);
    var datalist = $item.closest('.dl');
    var pagination = $(datalist).find('input.dl-pagination').first();
    if (!pagination.length) {
        // No such datalist or no pagination data
        return;
    }
    var dl_data = JSON.parse($(pagination).val());

    // Do we have an Ajax-URL?
    var ajaxurl = dl_data['ajaxurl'];
    if (ajaxurl === null) {
        return;
    }
    var pagesize = dl_data['pagesize'],
        rowsize = dl_data['rowsize'];

    var item_id = $item.attr('id');
    var item_list = item_id.split('-');
    var record_id = item_list.pop();

    // Ajax-delete the item
    $.ajax({
        'url': dlURLAppend(ajaxurl, 'delete=' + record_id),
        'success': function(data) {

            var row_index = $item.index(),
                row = $item.closest('.dl-row'),
                i, prev, next;

            // 1. Remove the item
            $item.remove();

            // 2. Move all following items in the row 1 position to the left
            var $row = $(row);
            if (row_index < rowsize - 1) {
                for (i=row_index + 1; i < rowsize; i++) {
                    prev = 'dl-col-' + (i-1);
                    next = 'dl-col-' + i;
                    $row.find('.' + next).removeClass(next).addClass(prev);
                }
            }
            
            // 3. Move all first items of all following rows to the end of the previous row
            var prev_row = row;
            $row.nextAll('.dl-row').each(function() {
                $(this).find('.dl-col-0').first()
                       .appendTo(prev_row)
                       .removeClass('dl-col-0')
                       .addClass('dl-col-' + (rowsize - 1));
                if (rowsize > 1) {
                    for (i=1; i < rowsize; i++) {
                        prev = 'dl-col-' + (i-1);
                        next = 'dl-col-' + i;
                        $(this).find('.' + next).removeClass(next).addClass(prev);
                    }
                }
                prev_row = this;
            });

            // 4. Load 1 more item to fill up the last row
            last_row = $row.closest('.dl').find('.dl-row').last();
            var numitems = $row.closest('.dl').find('.dl-item').length;
            
            $.ajax({
                'url': dlURLAppend(ajaxurl, 'start=' + numitems + '&limit=1'),
                'success': function(data) {
                    $(data.slice(data.indexOf('<')))
                        .find('.dl-item')
                        .first()
                        .removeClass('dl-col-0')
                        .addClass('dl-col-' + (rowsize - 1))
                        .appendTo(last_row);
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

            // Update dl-data totalitems/maxitems
            dl_data['totalitems']--;
            if (dl_data['maxitems'] > dl_data['totalitems']) {
                dl_data['maxitems'] = dl_data['totalitems'];
            }
            $(pagination).val(JSON.stringify(dl_data));

            // Also update the layer on the Map (if any)
            // @ToDo: Which Map?
            if (typeof map != 'undefined') {
                var layers = map.layers;
                var needle = item_list.join('_');
                Ext.iterate(layers, function(key, val, obj) {
                    if (key.s3_layer_id == needle) {
                        var layer = layers[val];
                        var found = false;
                        var uuid = data['uuid']; // The Record UUID
                        Ext.iterate(layer.feaures, function(key, val, obj) {
                            if (key.properties.id == uuid) {
                                // Remove the feature
                                layer.removeFeatures([key]);
                                found = true;
                            }
                        });
                        if (!found) {
                            // Feature was in a Cluster: refresh the layer
                            Ext.iterate(layer.strategies, function(key, val, obj) {
                                if (key.CLASS_NAME == 'OpenLayers.Strategy.Refresh') {
                                    // Reload the layer
                                    layer.strategies[val].refresh();
                                }
                            });
                        }
                    }
                });
            }
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

    var datalist = '#' + list_id;
    var $datalist = $(datalist);
    if (!$datalist.length) {
        return;
    }

    var pagination = $datalist.find('input.dl-pagination');
    if (!pagination.length) {
        // No pagination data
        return;
    }

    // Read dl_data
    var $pagination0 = $(pagination[0]);
    var dl_data = JSON.parse($pagination0.val());
    var startindex = dl_data['startindex'],
        pagesize = dl_data['pagesize'],
        maxitems = dl_data['maxitems'],
        totalitems = dl_data['totalitems'],
        ajaxurl = dl_data['ajaxurl'];

    if (pagesize === null) {
        // No pagination
        return;
    }

    if (filters) {
        try {
            ajaxurl = S3.search.filterURL(ajaxurl, filters);
            dl_data['ajaxurl'] = ajaxurl;
            $pagination0.val(JSON.stringify(dl_data));
        } catch(e) {}
    }

    var start = startindex;
    var limit = pagesize;

    // Ajax-load the list
    $.ajax({
        'url': dlURLAppend(ajaxurl, 'start=' + startindex + '&limit=' + pagesize),
        'success': function(data) {
            var newlist = $(data.slice(data.indexOf('<'))).find('.dl');
            $datalist.infinitescroll('destroy');
            $datalist.data('infinitescroll', null);
            if (newlist.length) {
                var pagination_new = $(newlist).find('input.dl-pagination');
                if (pagination_new.length) {
                    var dl_data_new = JSON.parse($(pagination_new[0]).val());
                    dl_data['totalitems'] = dl_data_new['totalitems'];
                    $pagination0.val(JSON.stringify(dl_data));
                }
                var modal_more = $datalist.find('a.s3_modal');
                if (modal_more.length) {
                    // Read attributes
                    var popup_url = $(modal_more[0]).attr('href');
                    var popup_title = $(modal_more[0]).attr('title');
                }
                $datalist.empty().html(newlist.html());
                $datalist.find('input.dl-pagination').replaceWith(pagination);
                if (modal_more.length) {
                    // Restore attributes
                    if (filters) {
                        popup_url = S3.search.filterURL(popup_url, filters);
                    }
                    $($datalist.find('.dl-navigation a')[0]).addClass('s3_modal')
                                                            .attr('href', popup_url)
                                                            .attr('title', popup_title);
                }
            } else {
                // List is empty
                var nav = $datalist.find('.dl-navigation').css({display: 'none'});
                newlist = $(data.slice(data.indexOf('<'))).find('.empty');
                $datalist.empty().append(newlist);
                $datalist.append(nav);
            }
            dlInfiniteScroll(datalist);
            $datalist.find('.dl-item:last:in-viewport').each(function() {
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

    var $datalist = $(datalist);
    var pagination = $datalist.find('input.dl-pagination');
    if (!pagination.length) {
        // No pagination
        return;
    }

    // Read dl_data
    var dl_data = JSON.parse($(pagination[0]).val());
    var startindex = dl_data['startindex'],
        maxitems = dl_data['maxitems'],
        totalitems = dl_data['totalitems'],
        pagesize = dl_data['pagesize'],
        ajaxurl = dl_data['ajaxurl'];

    if (!pagination.hasClass('dl-scroll')) {
        // No infiniteScroll
        if (pagesize > totalitems) {
            // Hide the 'more' button if we can see all items
            pagination.closest('.dl-navigation').css({display: 'none'});
        }
        return;
    }

    if (pagesize === null) {
        // No pagination
        pagination.closest('.dl-navigation').css({display: 'none'});
        return;
    }

    // Cannot retrieve more items than there are totally available
    maxitems = Math.min(maxitems, totalitems - startindex);

    // Compute bounds
    var maxindex = startindex + maxitems,
        initialitems = $datalist.find('.dl-item').length;

    // Compute maxpage
    var maxpage = 1,
        ajaxitems = (maxitems - initialitems);
    if (ajaxitems > 0) {
        maxpage += Math.ceil(ajaxitems / pagesize);
    } else {
        if (pagination.length) {
            pagination.closest('.dl-navigation').css({display: 'none'});
        }
        return;
    }

    if (pagination.length) {
        $datalist.infinitescroll({
            debug: false,
            loading: {
                // @ToDo: i18n
                finishedMsg: 'no more items to load',
                msgText: 'loading...',
                img: S3.Ap.concat('/static/img/indicator.gif')
            },
            navSelector: 'div.dl-navigation',
            nextSelector: 'div.dl-navigation a:first',
            itemSelector: 'div.dl-row',
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
                $(this).find('.dl-row:last:in-viewport').each(function() {
                    if (!$(this).hasClass('autoretrieve')) {
                        $(this).addClass('autoretrieve');
                        dlAutoRetrieve(this);
                    }
                });
            });
            dlItemBindEvents();
        });
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
        $(this).find('.dl-row:last:in-viewport').each(function() {
            $(this).addClass('autoretrieve');
            dlAutoRetrieve(this);
        });
    });

    // Bind events for newly loaded items
    dlItemBindEvents();
});

// END ========================================================================
