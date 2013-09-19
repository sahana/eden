/**
 * jQuery UI GroupedOpts Widget for S3GroupedOptionsWidget
 * 
 * @copyright: 2013 (c) Sahana Software Foundation
 * @license: MIT
 *
 * requires: jQuery 1.9.1+
 * requires: jQuery UI 1.10 widget factory
 *
 */

(function($, undefined) {
    
    var groupedoptsID = 0;

    $.widget('s3.groupedopts', {

        // default options
        options: {
            columns: 3
        },

        _create: function() {
            // create the widget
            var el = this.element.hide();
            
            this.id = groupedoptsID;
            groupedoptsID += 1;

            var multiple = el.attr('multiple');
            this.multiple = (typeof multiple != 'undefined') ? true : false;
            this.menu = null;

        },

        _init: function() {
            // update widget options
            this.refresh();
        },

        _destroy: function() {
            // remove generated elements & reset other changes
            this.menu.remove();
            this.element.show();
        },

        refresh: function() {
            // re-draw contents
            var el = this.element;
            
            this.index = 0;
            this.name = 's3-groupedopts-' + groupedoptsID;
            if (this.menu) {
                this.menu.remove();
            }
            this.selected = el.val();

            var groups = el.find('optgroup'), i;
            if (groups.length) {
                this.grouped = true;
                this.menu = $('<div class="s3-groupedopts-widget"/>');
                for (i=0; i<groups.length; i++) {
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

        _renderGroup: function(optgroup) {
            // Render a group
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

        _renderRows: function(items, group) {
            // Render all rows in a group
            var cols = this.options.columns, head = [], tail = items, pos = 0, size, item;

            while(tail.length) {
                size = Math.min(cols, tail.length);
                if (tail.length > size) {
                    head = tail.slice(0, size);
                    tail = tail.slice(size, tail.length);
                } else {
                    head = tail;
                    tail = [];
                }
                var row = $('<tr/>');
                for (var i=0; i<head.length; i++) {
                    item = head[i];
                    this._renderItem(item, row);
                }
                group.append(row);
            }
        },

        _renderItem: function(item, row) {
            // Render one checkbox item

            var $item = $(item),
                id = 's3-groupedopts-option-' + this.id + '-' + this.index,
                type = this.multiple ? 'checkbox' : 'radio';
                
            this.index += 1;
            
            var value = $item.val(),
                label = $item.html(),
                title = $item.attr('title');
                
            var olabel = '<label for="' + id + '"';
            if (title && title != '') {
                olabel += ' title="' + title + '"';
            }
            olabel += '>' + label + '</label>';

            var oinput = $('<input '+
                           'type="' + type + '" ' +
                           'id="' + id + '" ' +
                           'name="' + this.name + '" ' +
                           'class="s3-groupedopts-option" ' +
                           'value="' + value + '"/>'),
                pos;

            if (this.multiple) {
                pos = $.inArray(value, this.selected);
            } else {
                pos = value == this.selected ? 1 : -1;
            }
            if (pos >= 0) {
                $(oinput).prop('checked', true);
            }
            
            widget = $('<td>').append(oinput).append($(olabel));
            row.append(widget);
        },

        _bindEvents: function() {
            // bind events to generated elements

            var self = this;
            self.menu.find('.s3-groupedopts-option').click(function() {
                var value = $(this).val(),
                    el = self.element,
                    multiple = self.multiple;
                var selected = el.val();

                if (selected === null && multiple) {
                    selected = [];
                }
                if (multiple) {
                    var pos = $.inArray(value, selected);
                    if ($(this).is(':checked')) {
                        if (pos < 0) {
                            selected.push(value);
                        }
                    } else {
                        if (pos >= 0) {
                            selected.splice(pos, 1);
                        }
                    }
                } else {
                    if ($(this).is(':checked')) {
                        selected = value;
                    }
                }
                this.selected = selected;
                el.val(selected).change();
            });

            self.menu.find('.s3-groupedopts-label').click(function() {
                var div = $(this);
                div.next('table').toggle();
                div.toggleClass('expanded');
            });
        }
    });
})(jQuery);
