/**
 * jQuery UI GroupedOpts Widget for S3GroupedOptionsWidget
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
    var groupedoptsID = 0;

    /**
     * GroupedOpts widget, renders a SELECT as groups of checkboxes/radio buttons.
     */
    $.widget('s3.groupedopts', {

        /**
         * Default options
         *
         * @prop {number} columns - the number of columns
         * @prop {string} emptyText - message to show when no options are available
         * @prop {string} orientation - the ordering orientation,
         *                              'columns' (columns=>rows), or
         *                              'rows' (rows=>columns)
         * @prop {bool} sort - alpha-sort the options
         * @prop {bool} table - render options inside an HTML TABLE
         * @prop {string} comment - HTML template to render after the LABELs
         */
        options: {
            columns: 3,
            emptyText: 'No options available',
            orientation: 'columns',
            sort: true,
            table: true,
            comment: ''
        },

        /**
         * Create the widget
         */
        _create: function() {

            var el = this.element.hide();

            this.id = groupedoptsID;
            groupedoptsID += 1;

            var multiple = el.attr('multiple');
            if (multiple !== undefined) {
                this.multiple = true;
            } else {
                this.multiple = false;
            }
            this.menu = null;
        },

        /**
         * Update widget options
         */
        _init: function() {

            this.refresh();
        },

        /**
         * Remove generated elements & reset other changes
         */
        _destroy: function() {
            this.menu.remove();
            this.element.show();
        },

        /**
         * Re-draw contents
         */
        refresh: function() {

            var el = this.element,
                opts = this.options;

            this.index = 0;
            this.name = 's3-groupedopts-' + this.id;
            if (this.menu) {
                this.menu.remove();
            }
            this.selected = el.val();

            var groups = el.find('optgroup');
            if (!el.find('option').length) {
                this.grouped = true;
                this.menu = $('<div class="s3-groupedopts-widget">' +
                              '<span class="no-options-available">' +
                              opts.emptyText +
                              '</span></div>');
            } else
            if (groups.length) {
                this.grouped = true;
                this.menu = $('<div class="s3-groupedopts-widget"/>');
                for (var i=0; i < groups.length; i++) {
                    this._renderGroup(groups[i]);
                }
            } else {
                this.grouped = false;
                if (opts.table) {
                    this.menu = $('<table class="s3-groupedopts-widget"/>');
                } else {
                    this.menu = $('<div class="s3-groupedopts-widget"/>');
                }
                var items = el.find('option');
                this._renderRows(items, this.menu);
            }
            el.after(this.menu);
            this._bindEvents();
        },

        /**
         * Hide the menu
         */
        hide: function() {

            this.menu.hide();
        },

        /**
         * Show (un-hide) the menu
         */
        show: function() {

            this.menu.show();
        },

        /**
         * Test whether the menu is currently visible
         */
        visible: function() {

            return this.menu.is(':visible');
        },

        /**
         * Render a group
         *
         * @param {jQuery} optgroup - the optgroup element
         */
        _renderGroup: function(optgroup) {

            var label = $(optgroup).attr('label'),
                items = $(optgroup).find('option');

            if (items.length) {
                var group_label = $('<div class="s3-groupedopts-label">' + label + '</div>');
                this.menu.append(group_label);
                if (this.options.table) {
                    var group = $('<table class="s3-groupedopts-widget">');
                } else {
                    var group = $('<div class="s3-groupedopts-widget">');
                }
                this._renderRows(items, group);
                $(group).hide();
                this.menu.append(group);
            }
        },

        /**
         * Render all rows in a group
         *
         * @param {jQuery} items - the option elements in the group
         * @param {jQuery} group - the target table element
         */
        _renderRows: function(items, group) {

            var opts = this.options,
                numcols = opts.columns,
                tail = $.makeArray(items);

            if (opts.sort) {
                tail.sort(function(x, y) {
                    if ($(x).text() < $(y).text()) {
                        return -1;
                    } else {
                        return 1;
                    }
                });
            }

            var rows = [], i, j;
            if (opts.orientation == 'columns') {
                // Order items as columns=>rows
                var numrows = Math.ceil(tail.length / numcols);
                for (i = 0; i < numcols; i++) {
                    for (j = 0; j < numrows; j++) {
                        if (tail.length) {
                            if (rows.length < j + 1) {
                                rows.push([]);
                            }
                            rows[j].push(tail.shift());
                        }
                    }
                }
            } else {
                // Order items as rows=>columns
                while(tail.length) {
                    var row = [];
                    for (i=0; i < numcols; i++) {
                        if (!tail.length) {
                            break;
                        }
                        row.push(tail.shift());
                    }
                    rows.push(row);
                }
            }
            // Render the rows
            var table = opts.table;
            for (i = 0; i < rows.length; i++) {
                if (table) {
                    var tr = $('<tr/>');
                } else {
                    var tr = $('<div class="s3-groupedopts-row"/>');
                }
                for (j = 0; j < rows[i].length; j++) {
                    this._renderItem(rows[i][j], tr, table);
                }
                group.append(tr);
            }
        },

        /**
         * Render one checkbox/radio item
         *
         * @param {jQuery} item - the option element
         * @param {jQuery} row - the target element (e.g. tr)
         * @param {jQuery} table - whether to render as a table or not
         */
        _renderItem: function(item, row, table) {

            var comment = this.options.comment,
                multiple = this.multiple;

            var $item = $(item),
                id = 's3-groupedopts-option-' + this.id + '-' + this.index,
                type = multiple ? 'checkbox' : 'radio';

            this.index += 1;

            var value = $item.val(),
                label = $item.html(),
                title = $item.attr('title'),
                selected = this.selected;

            var olabel = '<label for="' + id + '"';
            if (title && title !== '') {
                olabel += ' title="' + title + '"';
            }
            if ((!multiple) && (value != selected)) {
                // Radio labels have a class for unselected items (to be able to make these appear as clickable hyperlinks)
                olabel += ' class="inactive"';
            }
            olabel += '>' + label + '</label>';

            var oinput = $('<input '+
                           'type="' + type + '" ' +
                           'id="' + id + '" ' +
                           'name="' + this.name + '" ' +
                           'class="s3-groupedopts-option" ' +
                           'value="' + value + '"/>'),
                pos;

            if (multiple) {
                pos = $.inArray(value, selected);
            } else {
                pos = value == selected ? 1 : -1;
            }
            if (pos >= 0) {
                $(oinput).prop('checked', true);
            }

            if (table) {
                var widget = $('<td>').append(oinput).append($(olabel));
            } else {
                var widget = $('<div class="s3-groupedopts-item">').append(oinput).append($(olabel));
            }
            if (comment) {
                 _.templateSettings = {interpolate: /\{(.+?)\}/g};
                var template = _.template(comment);
                var ocomment = template({v: value});
                widget.append($(ocomment));
            }
            row.append(widget);
        },

        /**
         * Bind events to generated elements
         */
        _bindEvents: function() {

            var self = this;
            self.menu.find('.s3-groupedopts-option').click(function() {
                var $this = $(this);
                var value = $this.val(),
                    el = self.element,
                    multiple = self.multiple;
                var selected = el.val();

                if (selected === null && multiple) {
                    selected = [];
                }
                if (multiple) {
                    var pos = $.inArray(value, selected);
                    if ($this.is(':checked')) {
                        if (pos < 0) {
                            selected.push(value);
                        }
                    } else {
                        if (pos >= 0) {
                            selected.splice(pos, 1);
                        }
                    }
                } else {
                    if ($this.is(':checked')) {
                        selected = value;
                        self.menu.find('.s3-groupedopts-option').each(function() {
                            $this = $(this);
                            if ($this.is(':checked')) {
                                $this.next().removeClass('inactive');
                            } else {
                                $this.next().addClass('inactive');
                            }
                        });
                    }
                }
                this.selected = selected;
                el.val(selected).change();
            });

            // Apply cluetip (from S3.js)
            self.menu.find('label[title]').cluetip({splitTitle: '|', showTitle:false});

            self.menu.find('.s3-groupedopts-label').click(function() {
                var div = $(this);
                div.next('table').toggle();
                div.toggleClass('expanded');
            });
        }
    });
})(jQuery);
