/**
 * jQuery UI HierarchicalOpts Widget for S3HierarchyFilter
 * 
 * @copyright: 2013 (c) Sahana Software Foundation
 * @license: MIT
 *
 * requires: jQuery 1.9.1+
 * requires: jQuery UI 1.10 widget factory
 * requires: jQuery JStree 1.0
 * 
 * status: experimental
 * 
 */

(function($, undefined) {

    var hierarchicaloptsID = 0;

    $.widget('s3.hierarchicalopts', {

        // Default options
        options: {
            selected: null,
            hint: 'Select'
        },

        _create: function() {
            // Create the widget
            var el = $(this.element),
                hint = this.options.hint;

            this.id = hierarchicaloptsID;
            hierarchicaloptsID += 1;

            this._namespace = '.hierarchicalopts' + hierarchicaloptsID;
            
            this.treeID = el.attr('id') + '-tree';

            // The hidden input field
            this.input = el.find('.s3-hierarchy-input').first();

            // The button
            this.button = $('<button type="button" class="s3-hierarchy-button ui-multiselect ui-widget ui-state-default ui-corner-all"><span class="ui-icon ui-icon-triangle-1-s"></span><span>' + hint + '</span></button>');

            // The tree
            this.tree = el.find('.s3-hierarchy-tree').first().hide().before(this.button);
            this._isOpen = false;
        },

        _init: function() {
            // Update widget options
            this.refresh();
        },

        _destroy: function() {
            // Remove generated elements & reset other changes
            $.Widget.prototype.destroy.call(this);
            
            this._unbindEvents();
            $(this.button).remove();
            $(this.tree).show();
        },

        refresh: function() {
            // Re-draw contents
            this._unbindEvents();

            var opts = this.options;
            
            var selected = [], s = opts.selected;
            if (s) {
                var treeID = this.treeID;
                for (var i=0, len=s.length; i<len; i++) {
                    selected.push(treeID + '-' + s[i]);
                }
            }

            $.jstree._themes = S3.Ap.concat('/static/styles/jstree/');
            if ($('body').css('direction') == 'ltr') {
                rtl = false;
            } else {
                rtl = true;
            }
            if (rtl) {
                theme = 'default-rtl';
            } else {
                theme = 'default';
            }
            this.tree.jstree({
                'core': {
                    animation: 100,
                    rtl: rtl
                },
                'themes': {
                    'theme' : theme,
                    'icons': false
                },
                'ui': {
                    'initially_select' : selected
                },
                'checkbox': {
                    'override_ui': true
                },
                'plugins': ['themes', 'html_data', 'ui', 'checkbox', 'sort']
            });

            this._bindEvents();
        },

        _updateSelectedNodes: function(data) {
            // Get all selected nodes and store the result in the hidden input

            var old_selected = this.input.val(),
                new_selected = [];

            if (old_selected) {
                old_selected = JSON.parse(old_selected);
            } else {
                old_selected = [];
            }

            var nodes = this.tree.jstree('get_checked', null, true)
                
            $(nodes).each(function() {
                var id = $(this).attr('id');
                if (id) {
                    id = parseInt(id.split('-').pop());
                    if (id) {
                        new_selected.push(id);
                    }
                }
            });
            var changed = false,
                diff = $(new_selected).not(old_selected).get();
            if (diff.length) {
                changed = true;
            } else {
                diff = $(old_selected).not(new_selected).get();
                if (diff.length) {
                    changed = true;
                }
            }

            this.input.val(JSON.stringify(new_selected));
            if (changed) {
                $(this.element).trigger('select.s3hierarchy');
            }
            return true;
        },

        set: function(values) {
            // Check particular nodes (used by setCurrentFilters)

            this.tree.jstree('uncheck_all');
            if (values) {
                for (var i=0, len=values.length, node_id; i < len; i++) {
                    node = $('#' + this.treeID + '-' + values[i]);
                    this.tree.jstree('check_node', node);
                }
            }
        },

        get: function() {
            // Get all checked nodes (used by getCurrentFilters)

            var value = this.input.val();
            if (value) {
                return JSON.parse(value);
            } else {
                return [];
            }
        },

        reset: function() {
            // Uncheck all nodes (used by clearFilters)

            this.tree.jstree('uncheck_all');
            this._updateSelectedNodes();
            return;
        },

        open: function() {
            // Open the tree

            if (this._isOpen) {
                this._close();
            }
            
            var button = $(this.button);
            var pos = button.position();
            
            $(this.tree).css({
                position: 'absolute',
                top: pos.top + button.outerHeight() + 3,
                left: pos.left,
                minWidth: button.outerWidth(),
                'z-index': 999999
            }).show();
            this._isOpen = true;
            button.addClass('ui-state-active');
            $(this).trigger('open');
        },

        close: function() {
            // Close the tree
            
            $(this.tree).hide();
            this._isOpen = false;
            $(this.button).removeClass('ui-state-active');
            $(this).trigger('close');
        },

        _bindEvents: function() {
            // Bind events to generated elements (after refresh)

            var widget = this,
                tree = $(this.tree),
                button = $(this.button),
                namespace = this._namespace;

            tree.bind('check_node.jstree', function (event, data) {
                widget._updateSelectedNodes();
            }).bind('uncheck_node.jstree', function (event, data) {
                widget._updateSelectedNodes();
            });

            button.bind('click' + namespace, function() {
                if (!widget._isOpen) {
                    widget.open();
                } else {
                    widget.close();
                }
            }).bind('keyup' + namespace, function(event) {
                event.preventDefault();
                switch(event.keyCode) {
                    case 27: // esc
                    case 38: // up
                    case 37: // left
                        widget.close();
                        break;
                    case 39: // right
                    case 40: // down
                        widget.open();
                        break;
                }
            }).bind('mouseenter' + namespace, function() {
                if (!button.hasClass('ui-state-disabled')) {
                    $(this).addClass('ui-state-hover');
                }
            }).bind('mouseleave' + namespace, function() {
                $(this).removeClass('ui-state-hover');
            }).bind('focus' + namespace, function() {
                if (!button.hasClass('ui-state-disabled')) {
                    $(this).addClass('ui-state-focus');
                }
            }).bind('blur' + namespace, function() {
                $(this).removeClass('ui-state-focus');
            });
            $(document).bind('mousedown' + namespace, function(event) {
                var target = event.target
                if (!tree.is(target) && !button.is(target) &&
                    tree.has(event.target).length === 0 &&
                    button.has(event.target).length === 0) {
                    widget.close();
                }
            });
            return true;
        },
        
        _unbindEvents: function() {
            // Unbind events (before refresh)

            var tree = $(this.tree),
                button = $(this.button),
                namespace = this._namespace;

            tree.unbind('check_node.jstree')
                .unbind('uncheck_node.jstree');

            $(this.button).unbind(namespace);
            $(document).unbind(namespace);

            return true;
        }
    });
})(jQuery);
