/**
 * Used by data lists (views/datalist.html)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

(function($, undefined) {

    var datalistID = 0;

    $.widget('s3.datalist', {

        // Default options
        options: {

        },

        _create: function() {
            // Create the widget

            this.id = datalistID;
            datalistID += 1;

            return;
        },

        _init: function() {
            // Update widget options
            var el = this.element;

            this.hasInfiniteScroll = false;

            // Render all initial contents
            this.refresh();

            return;
        },

        _destroy: function() {
            // Remove generated elements & reset other changes

            // @todo: implement
            return;
        },

        refresh: function() {
            // Rre-draw contents

            // Unbind global events
            this._unbindEvents();

            // Initialize infinite scroll
            this._infiniteScroll();

            // (Re-)bind item events
            this._bindItemEvents();

            // Bind global events
            this._bindEvents();

            // Fire initial update event
            $datalist.trigger('listUpdate');
            
            return;
        },

        _infiniteScroll: function() {
            // Initialize infinite scroll for this data list

            var $datalist = $(this.element);

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

                var dl = this;
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
                        var url = dl._urlAppend(ajaxurl, 'start=' + start + '&limit=' + limit);
                        return url;
                    },
                    maxPage: maxpage

                },
                // Function to be called after Ajax-loading new data
                function(data) {
                    $datalist.find('.dl-row:last:in-viewport').each(function() {
                        // Last item is within the viewport, so try to
                        // load more items to fill the viewport
                        $this = $(this);
                        if (!$this.hasClass('autoretrieve')) {
                            // prevent further auto-retrieve attempts if this
                            // one doesn't produce any items:
                            $this.addClass('autoretrieve');
                            dl._autoRetrieve();
                        }
                    });
                    dl._bindItemEvents();
                });
                this.hasInfiniteScroll = true;

                $datalist.find('.dl-row:last:in-viewport').each(function() {
                    $(this).addClass('autoretrieve');
                    dl._autoRetrieve();
                });
            }
            return;
        },

        ajaxReloadItem: function(record_id) {
            // Reload a single item (e.g. when updated in a modal)

            var $datalist = $(this.element);

            var list_id = $datalist.attr('id'),
                pagination = $datalist.find('input.dl-pagination');

            if (!pagination.length) {
                // No pagination data
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
            var dl = this;
            $.ajax({
                'url': dl._urlAppend(ajaxurl, 'record=' + record_id),
                'success': function(data) {
                    var item_data = $(data.slice(data.indexOf('<'))).find(item_id);
                    if (item_data.length) {
                        item.replaceWith(item_data);
                    }
                    // Bind item events
                    dl._bindItemEvents();
                    
                    // Fire update event
                    $datalist.trigger('listUpdate');
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
            return;
        },

        ajaxReload: function(filters) {
            // Ajax-reload this datalist

            var $datalist = $(this.element);

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
            var dl = this;
            $.ajax({
                'url': dl._urlAppend(ajaxurl, 'start=' + startindex + '&limit=' + pagesize),
                'success': function(data) {
                    // Update the list

                    // Remove the infinite scroll
                    $datalist.infinitescroll('destroy');
                    $datalist.data('infinitescroll', null);
                    
                    var newlist = $(data.slice(data.indexOf('<'))).find('.dl');
                    if (newlist.length) {
                        // Insert new items, update status
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
                        // List is empty: hide navigation, show empty section
                        var nav = $datalist.find('.dl-navigation').css({display: 'none'});
                        newlist = $(data.slice(data.indexOf('<'))).find('.empty');
                        $datalist.empty().append(newlist);
                        $datalist.append(nav);
                    }

                    // Re-activate infinite scroll
                    dl._infiniteScroll();
                    $datalist.find('.dl-item:last:in-viewport').each(function() {
                        $(this).addClass('autoretrieve');
                        dl._autoRetrieve();
                    });

                    // Bind item events
                    dl._bindItemEvents();

                    // Fire update event
                    $datalist.trigger('listUpdate');
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
            return;
        },

        _ajaxDeleteItem: function(anchor) {
            // Ajax-delete an item from this list

            var $datalist = $(this.element);

            var item = $(anchor).closest('.dl-item');
            if (!item.length) {
                return;
            }
            var $item = $(item);

            var pagination = $datalist.find('input.dl-pagination').first();
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
            var dl = this;
            $.ajax({
                'url': this._urlAppend(ajaxurl, 'delete=' + record_id),
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
                        'url': dl._urlAppend(ajaxurl, 'start=' + numitems + '&limit=1'),
                        'success': function(data) {
                            $(data.slice(data.indexOf('<')))
                                .find('.dl-item')
                                .first()
                                .removeClass('dl-col-0')
                                .addClass('dl-col-' + (rowsize - 1))
                                .appendTo(last_row);
                            dl._bindItemEvents();
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

                    // 5. Update dl-data totalitems/maxitems
                    dl_data['totalitems']--;
                    if (dl_data['maxitems'] > dl_data['totalitems']) {
                        dl_data['maxitems'] = dl_data['totalitems'];
                    }
                    $(pagination).val(JSON.stringify(dl_data));

                    // 6. Show the empty-section if there are no more records
                    if (dl_data['totalitems'] == 0) {
                        $datalist.find('.dl-empty').css({display: 'block'});
                    }

                    // 7. Also update the layer on the Map (if any)
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

                    // 8. Fire update event
                    $datalist.trigger('listUpdate');
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

            $datalist.find('.dl-item:last:in-viewport').each(function() {
                $(this).addClass('autoretrieve');
                dl._autoRetrieve(this);
            });
            return;

        },

        _autoRetrieve: function() {
            // Force page retrieval
            if (this.hasInfiniteScroll) {
                $(this.element).infinitescroll('retrieve');
            }
            return;
        },

        _urlAppend: function(url, query) {
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
        },

        getTotalItems: function() {
            
            var $datalist = $(this.element);
            var pagination = $datalist.find('input.dl-pagination');
            if (!pagination.length) {
                return $datalist.find('.dl-item').length;
            }
            var $pagination0 = $(pagination[0]);
            var dl_data = JSON.parse($pagination0.val());
            return dl_data['totalitems'];
        },
        
        _bindItemEvents: function() {
            // Bind events in list items

            $datalist = $(this.element);

            // Click-event for dl-item-delete
            var dl = this;
            $datalist.find('.dl-item-delete')
                     .css({cursor: 'pointer'})
                     .unbind('click.dl')
                     .on('click.dl', function(event) {
                if (confirm(i18n.delete_confirmation)) {
                    dl._ajaxDeleteItem(this);
                    return true;
                } else {
                    event.preventDefault();
                    return false;
                }
            });

            // Add Event Handlers to new page elements
            S3.redraw();

            // Other callbacks

            return;
        },

        _bindEvents: function(data) {
            // Bind events to generated elements (after refresh)

            return;
        },

        _unbindEvents: function() {
            // Unbind events (before refresh)

            return;
        }
    });
})(jQuery);

/*
 * DataLists document-ready script - attach to all .dl
 */
$(document).ready(function() {

    // Initialize infinite scroll
    $('.dl').each(function() {
        $(this).datalist();
    });

});

// END ========================================================================
