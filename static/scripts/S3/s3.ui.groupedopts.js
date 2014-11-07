/**
 * jQuery UI GroupedOpts Widget for S3GroupedOptionsWidget
 * 
 * @copyright: 2013-14 (c) Sahana Software Foundation
 * @license: MIT
 *
 * requires: jQuery 1.9.1+
 * requires: jQuery UI 1.10 widget factory
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
         * @prop {string} order - the ordering direction, 
         *                        'columns' (columns=>rows) or 'rows' (rows=>columns)
         * @prop {bool} sort - alpha-sort the options
         */
        options: {
            columns: 3,
            emptyText: 'No options available',
            order: 'columns',
            sort: true
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

            var el = this.element;

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
                              this.options.emptyText +
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
                this.menu = $('<table class="s3-groupedopts-widget"/>');
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
                var group = $('<table class="s3-groupedopts-widget">');
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

            var numcols = this.options.columns,
                tail = $.makeArray(items);

            if (this.options.sort) {
                tail.sort(function(x, y) {
                    if ($(x).text() < $(y).text()) {
                        return -1;
                    } else {
                        return 1;
                    }
                });
            }

            var rows = [], i, j;
            if (this.options.order == 'columns') {
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
                    row = [];
                    for (i=0; i<numcols; i++) {
                        if (!tail.length) {
                            break;
                        }
                        row.push(tail.shift());
                    }
                    rows.push(row);
                }
            }
            // Render the rows
            for (i = 0; i<rows.length; i++) {
                var tr = $('<tr/>');
                for (j = 0; j<rows[i].length; j++) {
                    this._renderItem(rows[i][j], tr);
                }
                group.append(tr);
            }
        },

        /**
         * Render one checkbox/radio item
         * 
         * @param {jQuery} item - the option element
         * @param {jQuery} row - the target tr element
         */
        _renderItem: function(item, row) {

            var multiple = this.multiple;

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

            var widget = $('<td>').append(oinput).append($(olabel));
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
