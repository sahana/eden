/**
 * jQuery UI DataList Widget for "lists of data cards"
 * - server-side implementation is S3DataList in modules/s3/s3data.py
 *
 * @copyright 2013-2019 (c) Sahana Software Foundation
 * @license MIT
 *
 * requires jQuery 1.9.1+
 * requires jQuery UI 1.10 widget factory
 *
 */

(function($, undefined) {

    "use strict";

    /**
     * ajaxMethod: use $.searchS3 if available, fall back to $.ajaxS3
     */
    var ajaxMethod = $.ajaxS3;
    if ($.searchS3 !== undefined) {
        ajaxMethod = $.searchS3;
    }

    /**
     * Custom wrapper for $.infinitescroll.beginAjax(), to inject $.searchS3
     */
    var beginAjaxS3 = function(opts) {

        var method = 'html+callback';
        if (opts.dataType === 'html' || opts.dataType === 'json') {
            method = opts.dataType;
            if (opts.appendCallback && opts.dataType === 'html') {
                method += '+callback';
            }
        }

        if (method == 'html') {

            // increment the URL bit. e.g. /page/3/
            opts.state.currPage++;

            // Manually control maximum page
            if (opts.maxPage != undefined && opts.state.currPage > opts.maxPage ) {
                this.destroy();
                return;
            }

            var path = opts.path,
                desturl;
            if (typeof path === 'function') {
                desturl = path(opts.state.currPage);
            } else {
                desturl = path.join(opts.state.currPage);
            }

            var instance = this;
            ajaxMethod({
                // params
                url: desturl,
                type: 'GET', // explicit GET (to prevent $.searchS3 fall-through)
                dataType: opts.dataType,
                complete: function infscr_ajax_callback(jqXHR, textStatus) {

                    var box;
                    if ($(opts.contentSelector).is('table')) {
                        box = $('<tbody/>');
                    } else {
                        box = $('<div/>');
                    }

                    var condition = (typeof (jqXHR.isResolved) !== 'undefined') ? (jqXHR.isResolved()) : (textStatus === "success" || textStatus === "notmodified");
                    if (condition) {
                        instance._loadcallback(box, jqXHR.responseText, desturl);
                    } else {
                        instance._error('end');
                    }
                }
            });

        } else {
            this.prototype.beginAjax.call(this, opts);
        }
    };

    /**
     * Custom append-callback for $.infinitescroll,
     * applied by setting behavior='append' and appendCallback=false
     */
    $.infinitescroll.prototype._callback_append = function(data, url) {

        var frag = document.createDocumentFragment();

        data.each(function() {
            frag.appendChild(this);
        })
        $(this).get()[0].appendChild(frag);
    };

    var datalistID = 0;

    /**
     * DataList widget, pagination and Ajax-Refresh for data lists
     */
    $.widget('s3.datalist', {

        /**
         * Default options
         */
        options: {

        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = datalistID;
            datalistID += 1;
        },

        /**
         * Update widget options
         */
        _init: function() {

            this.hasInfiniteScroll = false;

            // Render all initial contents
            this.refresh();
        },

        /**
         * Remove generated elements & reset other changes
         */
        _destroy: function() {

            $.Widget.prototype.destroy.call(this);
        },

        /**
         * Re-draw contents
         */
        refresh: function() {

            // Unbind global events
            //this._unbindEvents();

            // Initialize infinite scroll
            this._infiniteScroll();

            // (Re-)bind item events
            this._bindItemEvents();

            // Bind global events
            //this._bindEvents();

            // Fire initial update event
            $(this.element).trigger('listUpdate');
        },

        /**
         * Initialize infinite scroll for this data list
         */
        _infiniteScroll: function() {

            var $datalist = $(this.element);

            var pagination = $datalist.find('input.dl-pagination');
            if (!pagination.length) {
                // No pagination
                return;
            }

            // Read pagination data
            var dlData = JSON.parse($(pagination[0]).val());
            var startIndex = dlData.startindex,
                maxItems = dlData.maxitems,
                totalItems = dlData.totalitems,
                pageSize = dlData.pagesize,
                ajaxURL = dlData.ajaxurl;

            if (!pagination.hasClass('dl-scroll')) {
                // No infiniteScroll
                if (pageSize > totalItems) {
                    // Hide the 'more' button if we can see all items
                    pagination.closest('.dl-navigation').css({display: 'none'});
                }
                return;
            }

            if (pageSize === null) {
                // No pagination
                pagination.closest('.dl-navigation').css({display: 'none'});
                return;
            }

            // Cannot retrieve more items than there are totally available
            maxItems = Math.min(maxItems, totalItems - startIndex);

            // Compute bounds
            var maxIndex = startIndex + maxItems,
                initialItems = $datalist.find('.dl-item').length;

            // Compute maxPage
            var maxPage = 1,
                ajaxItems = (maxItems - initialItems);
            if (ajaxItems > 0) {
                maxPage += Math.ceil(ajaxItems / pageSize);
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
                    // Use _callback_append instead of standard append-callback
                    appendCallback: false,
                    behavior: 'append',
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
                        var start = initialItems + (page - 2) * pageSize;
                        var limit = Math.min(pageSize, maxIndex - start);
                        // Construct Ajax URL
                        var url = dl._urlAppend(ajaxURL, 'start=' + start + '&limit=' + limit);
                        return url;
                    },
                    dataType: 'html',
                    maxPage: maxPage
                },
                // Function to be called after Ajax-loading and appending new data
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

                // Override beginAjax with custom method to inject $.searchS3 option
                var inst = $datalist.data("infinitescroll");
                inst.beginAjax = beginAjaxS3;

                this.hasInfiniteScroll = true;

                $datalist.find('.dl-row:last:in-viewport').each(function() {
                    $(this).addClass('autoretrieve');
                    dl._autoRetrieve();
                });
            }
            return;
        },

        /**
         * Reload a single item (e.g. when updated in a modal)
         *
         * @param {integer} recordID - the record ID
         */
        ajaxReloadItem: function(recordID) {

            var $datalist = $(this.element);

            var listID = $datalist.attr('id'),
                pagination = $datalist.find('input.dl-pagination');

            if (!pagination.length) {
                // No pagination data
                return;
            }

            // Do we have an Ajax-URL?
            var dlData = JSON.parse($(pagination[0]).val()),
                ajaxURL = dlData.ajaxurl;
            if (ajaxURL === null) {
                return;
            }

            // Is the item currently loaded?
            var itemID = '#' + listID + '-' + recordID,
                item = $(itemID);
            if (!item.length) {
                return;
            }

            // Ajax-load the item
            var dl = this;
            ajaxMethod({
                'url': dl._urlAppend(ajaxURL, 'record=' + recordID),
                'type': 'GET',
                'dataType': 'html',
                'success': function(data) {
                    var itemData = $(data.slice(data.indexOf('<'))).find(itemID);
                    if (itemData.length) {
                        item.replaceWith(itemData);
                    } else {
                        // Updated item does not match the filter anymore
                        dl._removeItem(item, dlData);
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
                }
            });
        },

        /**
         * Ajax-reload this datalist
         *
         * @param {Array} filters - the current filters
         */
        ajaxReload: function(filters) {

            var $datalist = $(this.element);

            var pagination = $datalist.find('input.dl-pagination');
            if (!pagination.length) {
                // No pagination data
                return;
            }

            // Read dlData
            var $pagination0 = $(pagination[0]);
            var dlData = JSON.parse($pagination0.val());
            var startIndex = dlData.startindex,
                pageSize = dlData.pagesize,
                totalItems = dlData.totalitems,
                ajaxURL = dlData.ajaxurl;

            if (pageSize === null) {
                // No pagination
                return;
            }

            // Handle filters
            if (typeof filters == 'undefined') {
                // Find a filter form that has the current datalist as target
                var listID = $datalist.attr('id'),
                    filterTargets = $('form.filter-form input.filter-submit-target'),
                    len = filterTargets.length,
                    targets,
                    targetList;
                if (listID && len) {
                    for (var i = 0; i < len; i++) {
                        targets = $(filterTargets[i]);
                        targetList = targets.val().split(' ');
                        if ($.inArray(listID, targetList) != -1) {
                            filters = S3.search.getCurrentFilters(targets.closest('form.filter-form'));
                            break;
                        }
                    }
                }
            }
            if (filters) {
                // Update the Ajax URL
                try {
                    ajaxURL = S3.search.filterURL(ajaxURL, filters);
                    dlData.ajaxurl = ajaxURL;
                    $pagination0.val(JSON.stringify(dlData));
                } catch(e) {}
            }

            var start = startIndex,
                limit = pageSize;

            // Ajax-load the list
            var dl = this;
            ajaxMethod({
                'url': dl._urlAppend(ajaxURL, 'start=' + startIndex + '&limit=' + pageSize),
                'type': 'GET',
                'dataType': 'html',
                'success': function(data) {
                    // Update the list

                    // Remove the infinite scroll
                    $datalist.infinitescroll('destroy');
                    $datalist.data('infinitescroll', null);

                    var newlist = $(data.slice(data.indexOf('<'))).find('.dl');
                    if (newlist.length) {
                        // Insert new items, update status
                        var paginationNew = $(newlist).find('input.dl-pagination');
                        if (paginationNew.length) {
                            var dlDataNew = JSON.parse($(paginationNew[0]).val());
                            dlData.totalitems = dlDataNew.totalitems;
                            dlData.maxitems = dlDataNew.maxitems;
                            $pagination0.val(JSON.stringify(dlData));
                        }
                        var modalMore = $datalist.find('div.dl-navigation a.dl-more'),
                            modalMoreLength = modalMore.length,
                            popup_url,
                            popup_title;
                        if (modalMoreLength) {
                            // Read attributes
                            popup_url = $(modalMore[0]).attr('href');
                            popup_title = $(modalMore[0]).attr('title');
                        }
                        $datalist.empty().html(newlist.html());
                        $datalist.find('input.dl-pagination').replaceWith(pagination);
                        if (modalMoreLength) {
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
                }
            });
            return;
        },

        /**
         * Ajax-delete an item from this list
         *
         * @param {jQuery} anchor - the card element that triggered the action
         */
        _ajaxDeleteItem: function(anchor) {

            var $datalist = $(this.element);

            var item = $(anchor).closest('.dl-item');
            if (!item.length) {
                return;
            }

            var pagination = $datalist.find('input.dl-pagination').first();
            if (!pagination.length) {
                // No such datalist or no pagination data
                return;
            }
            var dlData = JSON.parse($(pagination).val());

            // Do we have an Ajax-URL?
            var ajaxURL = this._stripFilters(dlData.ajaxurl);
            if (ajaxURL === null) {
                return;
            }

            var recordID = item.attr('id').split('-').pop();

            // Ajax-delete the item
            var dl = this;
            ajaxMethod({
                'url': this._urlAppend(ajaxURL, 'delete=' + recordID),
                'type': 'POST',
                'dataType': 'json',
                'success': function(data) {
                    // Remove the card
                    dl._removeItem(item, dlData);
                },
                'error': function(request, status, error) {
                    var msg;
                    if (error == 'UNAUTHORIZED') {
                        msg = i18n.gis_requires_login;
                    } else {
                        msg = request.responseText;
                    }
                    console.log(msg);
                }
            });

            // Trigger auto-retrieve
            $datalist.find('.dl-item:last:in-viewport').each(function() {
                $(this).addClass('autoretrieve');
                dl._autoRetrieve(this);
            });
        },

        /**
         * Remove an item from the list
         *
         * @param {jQuery} item - the list item (card)
         * @param {object} dlData - the pagination data
         */
        _removeItem: function(item, dlData) {

            var $datalist = $(this.element),
                pagination = $datalist.find('input.dl-pagination').first(),
                rowSize = dlData.rowsize,
                ajaxURL = dlData.ajaxurl;

            var rowIndex = item.index(),
                row = item.closest('.dl-row'),
                idTokens = item.attr('id').split('-'),
                i,
                prev,
                next;

            // 1. Remove the item
            item.remove();

            // 2. Move all following items in the row 1 position to the left
            var $row = $(row);
            if (rowIndex < rowSize - 1) {
                for (i = rowIndex + 1; i < rowSize; i++) {
                    prev = 'dl-col-' + (i - 1);
                    next = 'dl-col-' + i;
                    $row.find('.' + next).removeClass(next).addClass(prev);
                }
            }

            // 3. Move all first items of all following rows to the end of the previous row
            var prevRow = row;
            $row.nextAll('.dl-row').each(function() {
                $(this).find('.dl-col-0').first()
                    .appendTo(prevRow)
                    .removeClass('dl-col-0')
                    .addClass('dl-col-' + (rowSize - 1));
                if (rowSize > 1) {
                    for (i = 1; i < rowSize; i++) {
                        prev = 'dl-col-' + (i - 1);
                        next = 'dl-col-' + i;
                        $(this).find('.' + next).removeClass(next).addClass(prev);
                    }
                }
                prevRow = this;
            });

            // 4. Load 1 more item to fill up the last row
            var lastRow = $row.closest('.dl').find('.dl-row').last(),
                numItems = $row.closest('.dl').find('.dl-item').length;

            var dl = this;
            ajaxMethod({
                'url': dl._urlAppend(ajaxURL, 'start=' + numItems + '&limit=1'),
                'type': 'GET',
                'dataType': 'html',
                'success': function(data) {
                    // @todo: reduce counters (total items, max items)
                    // and update header accordingly
                    $(data.slice(data.indexOf('<')))
                        .find('.dl-item')
                        .first()
                        .removeClass('dl-col-0')
                        .addClass('dl-col-' + (rowSize - 1))
                        .appendTo(lastRow);
                    dl._bindItemEvents();
                },
                'error': function(request, status, error) {
                    if (error == 'UNAUTHORIZED') {
                        msg = i18n.gis_requires_login;
                    } else {
                        msg = request.responseText;
                    }
                    console.log(msg);
                }
            });

            // 5. Update dl-data totalitems/maxitems
            dlData.totalitems--;
            if (dlData.maxitems > dlData.totalitems) {
                dlData.maxitems = dlData.totalitems;
            }
            $(pagination).val(JSON.stringify(dlData));

            // 6. Show the empty-section if there are no more records
            if (dlData.totalitems === 0) {
                $datalist.find('.dl-empty').css({display: 'block'});
            }

            // 7. Also update the layer on the Map (if any)
            // @ToDo: Which Map?
            if (typeof map != 'undefined') {
                var layers = map.layers,
                    needle = idTokens.join('_');
                Ext.iterate(layers, function(key, val, obj) {
                    if (key.s3_layer_id == needle) {
                        var layer = layers[val],
                            found = false,
                            uuid = data['uuid']; // The Record UUID
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

        /**
         * Force page retrieval
         */
        _autoRetrieve: function() {

            if (this.hasInfiniteScroll) {
                $(this.element).infinitescroll('retrieve');
            }
        },

        /**
         * Append extra query elements to a URL
         *
         * @param {string} url - the URL
         * @param {string} query - the additional query
         */
        _urlAppend: function(url, query) {

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

        /**
         * Remove all filters from a URL
         *
         * @param {string} url - the URL
         * @returns {string} - the URL without filters
         */
        _stripFilters: function(url) {

            if (!url) {
                return null;
            }

            var urlparts = url.split('?');
            if (urlparts.length >= 2) {

                var queries = urlparts[1].split(/[&;]/g);
                for (var i = queries.length; i-- > 0;) {
                    if (queries[i].split('=')[0].lastIndexOf('.', 1) != -1) {
                        queries.splice(i, 1);
                    }
                }
                url = urlparts[0] + (queries.length > 0 ? '?' + queries.join('&') : "");
            }
            return url;
        },

        /**
         * Get the total number of items (from the data dict)
         */
        getTotalItems: function() {

            var pagination = $(this.element).find('input.dl-pagination');
            if (!pagination.length) {
                // No pagination = all items in the list, so just count them
                return $datalist.find('.dl-item').length;
            }

            return JSON.parse($(pagination[0]).val())['totalitems'];
        },

        /**
         * Bind events in list items
         *
         * @todo: call from _bindEvents?
         */
        _bindItemEvents: function() {
            // Bind events in list items

            var $datalist = $(this.element);

            // Click-event for dl-item-delete
            var dl = this;
            $datalist.find('.dl-item-delete')
                     .css({cursor: 'pointer'})
                     .off('click.dl')
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

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            return true;
        }
    });

    /**
     * DataLists document-ready script - attach to all .dl
     */
    $(document).ready(function() {

        // Initialize infinite scroll
        $('.dl').each(function() {
            $(this).datalist();
        });
    });

})(jQuery);

// END ========================================================================
